#!/usr/bin/env python3

import collections
import dataclasses
import dlib  # type: ignore
import logging
import math
import numpy
import os
import os.path
import PIL.Image  # type: ignore
import PIL.ImageFile  # type: ignore
import subprocess
import tempfile
import typing

ImageSize = collections.namedtuple(
    "ImageSize", ["x", "y", "extra_convert_params"])
ThumbnailCreateParams = typing.Tuple[ImageSize, str, ImageSize, str]
# Disable decompression bomb protection. This is required to process
# some PNG images with PIL...
PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True


def get_image_size(filename: str) -> ImageSize:
    try:
        image = PIL.Image.open(filename)
    except Exception as e:
        logging.error("Unable to open %s: %s", filename, e)
        raise e
    x, y = image.size
    return ImageSize(x, y, [])


def optimize_png(source: str) -> None:
    temporary_png = "%s.zpng" % source
    run_optipng = True
    #try:
    #    subprocess.check_call(
    #        ['zopflipng', '-m', '-y', source, temporary_png])
    # There are bugs either in GraphicsMagick or zopflipng that can
    # fail zopflipng. Run optipng in that case.
    #except subprocess.CalledProcessError as e:
    #    logging.warning("Unable to run zopflipng on %r", source)
    #    run_optipng = True
    if run_optipng:
        subprocess.check_call(
            ['optipng', '-o7', '-out', temporary_png, source])
    subprocess.check_call(['mv', temporary_png, source])


@dataclasses.dataclass
class FaceInfo:
    confidence: float
    left: int
    top: int
    right: int
    bottom: int

    def __str__(self) -> str:
        return "%f %d %d %d %d" % (
            self.confidence,
            self.left,
            self.top,
            self.right,
            self.bottom,
        )


@dataclasses.dataclass
class FaceDetectData:
    fd_algorithm: str
    fd_data_id: str
    fd_parameters: str
    image_width: int
    image_height: int
    faces: typing.List[FaceInfo]


def load_face_detect_data(filename: str) -> typing.Optional[FaceDetectData]:
    if not os.path.exists(filename):
        return None
    data = ""
    with open(filename) as fp:
        data = fp.read()

    lines = data.splitlines()
    fd_algorithm = lines[0]
    fd_data_id = lines[1]
    fd_parameters = lines[2]
    image_size_str = lines[3]
    image_width, image_height = [
        int(x) for x in image_size_str.split()]
    faces: typing.List[FaceInfo] = []
    for face_line in lines[4:]:
        (confidence_str,
         left_str,
         top_str,
         right_str,
         bottom_str) = face_line.split()
        faces.append(FaceInfo(
            confidence=float(confidence_str),
            left=int(left_str),
            top=int(top_str),
            right=int(right_str),
            bottom=int(bottom_str),
        ))
    return FaceDetectData(
        fd_algorithm=fd_algorithm,
        fd_data_id=fd_data_id,
        fd_parameters=fd_parameters,
        image_width=image_width,
        image_height=image_height,
        faces=faces,
    )


def atomic_write_file(filename: str, data: str) -> None:
    tempfile_name = None
    try:
        with tempfile.NamedTemporaryFile(
                dir=os.path.dirname(filename),
                mode="w",
                delete=False) as fp:
            tempfile_name = fp.name
            fp.write(data)
    except Exception:
        assert tempfile_name is not None
        os.unlink(tempfile_name)
        raise
    os.rename(tempfile_name, filename)


def save_face_detect_data(filename: str, data: FaceDetectData) -> None:
    out_image_data = """\
%(fd_algorithm)s
%(fd_data_id)s
%(fd_parameters)s
%(image_width)d %(image_height)d
""" % dataclasses.asdict(data)
    faces_str = "\n".join(str(x) for x in data.faces)
    if faces_str:
        faces_str += "\n"
    atomic_write_file(filename, out_image_data + faces_str)


def resize_image(image: numpy.ndarray, max_pixels: int) -> numpy.ndarray:
    width, height, _ = image.shape
    scaling_factor = math.sqrt(float(max_pixels) / (width * height))
    new_width = int(scaling_factor * width)
    new_height = int(scaling_factor * height)
    logging.warning(
        "Picture size %dx%d = %d pixels > %d pixels. "
        "Scaling to %dx%d",
        width,
        height,
        width * height,
        max_pixels,
        new_width,
        new_height)
    return dlib.resize_image(image, cols=new_width, rows=new_height)


class FaceDetector:
    def __init__(self, datafile: str):
        self.algorithm = "dlib.cnn_face_detection_model_v1"
        self.data_id = os.path.basename(datafile)
        self.detector = dlib.cnn_face_detection_model_v1(datafile)

    def __call__(self, original_image: str) -> typing.Optional[FaceDetectData]:
        face_detect_file = original_image + ".faces.txt"
        face_detect_data = load_face_detect_data(face_detect_file)
        if face_detect_data is not None:
            return face_detect_data

        try:
            image = dlib.load_rgb_image(original_image)
        except RuntimeError as e:
            logging.warning("Unable to load image %r: %r", original_image, e)
            return None
        width, height, _ = image.shape

        upscales = 1
        # Around 9M pixels we exceed 32 GB memory limits when upscaling.
        max_image_pixels = 7300000
        if width * height > max_image_pixels:
            image = resize_image(image, max_image_pixels)
        detections = self.detector(image, upscales)
        if detections is None:
            return None

        faces: typing.List[FaceInfo] = []
        for detection in detections:
            faces.append(
                FaceInfo(
                    confidence=detection.confidence,
                    left=detection.rect.left(),
                    top=detection.rect.top(),
                    right=detection.rect.right(),
                    bottom=detection.rect.bottom(),
                ))

        face_detect_data = FaceDetectData(
            fd_algorithm=self.algorithm,
            fd_data_id=self.data_id,
            fd_parameters="upscales=%d" % upscales,
            image_width=width,
            image_height=height,
            faces=faces,
        )

        save_face_detect_data(face_detect_file, face_detect_data)
        return face_detect_data


def create_thumbnail(
        original_size: ImageSize,
        original_image: str,
        target_size: ImageSize,
        target_file: str) -> None:
    if os.path.exists(target_file):
        return
    temporary_resized_fp = tempfile.NamedTemporaryFile(
        prefix=".thumbnail-", suffix=".png")
    temporary_resized_image = temporary_resized_fp.name

    upscaled_x = 0
    source_image = original_image
    if original_size.x < target_size.x:
        temporary_nearest_neighbor_fp = tempfile.NamedTemporaryFile(
            prefix=".thumbnail-nn-", suffix=".png")
        temporary_nearest_neighbor_image = temporary_nearest_neighbor_fp.name
        upscaled_multiplier = int(math.ceil(float(target_size.x) / original_size.x))
        upscaled_x = original_size.x * upscaled_multiplier
        upscaled_percentage = 100 * upscaled_multiplier
        subprocess.check_call(
            ['convert', source_image, '-scale', '%d%%' % upscaled_percentage,
             temporary_nearest_neighbor_image])
        source_image = temporary_nearest_neighbor_image


    if target_size.x == upscaled_x:
        temporary_resized_image = source_image
    else:
        subprocess.check_call(
            ['convert', source_image, '-resize', '%dx20000' % target_size.x,
             temporary_resized_image])

    # XXX hack
    convert_params = []
    if target_file.endswith(".jpeg"):
        convert_params = target_size.extra_convert_params
    if target_size.y is not None:
        target_crop_size = "%dx%d" % (target_size.x, target_size.y)
        convert_call = [
            'convert',
            '-gravity',
            'Center',
            '-crop',
            '%s+0+0' % target_crop_size,
            '+repage'] + convert_params
        subprocess.check_call(
            convert_call + [temporary_resized_image, target_file])
    else:
        subprocess.check_call(
            (["convert"]
             + convert_params
             + [temporary_resized_image, target_file]))

    #if target_file.endswith(".jpeg"):
    #    subprocess.check_call(['jpegoptim', '--strip-all', target_file])
    #if target_file.endswith(".png"):
    #    optimize_png(target_file)


def create_thumbnails_tasks(
        original_image: str,
        target_prefix: str,
        default_size: ImageSize,
        extra_sizes: typing.List[ImageSize]) -> typing.List[ThumbnailCreateParams]:
    creations = []
    size = get_image_size(original_image)
    default_jpeg = "%s-%dw.jpeg" % (target_prefix, default_size.x)
    if not os.path.exists(default_jpeg):
        creations.append((size, original_image, default_size, default_jpeg))
    default_png = "%s-%dw.png" % (target_prefix, default_size.x)
    if not os.path.exists(default_png):
        creations.append((size, original_image, default_size, default_png))

    for extra_size in extra_sizes:
        extra_jpeg = "%s-%dw.jpeg" % (target_prefix, extra_size.x)
        extra_png = "%s-%dw.png" % (target_prefix, extra_size.x)
        # if size.x < extra_size.x:
        #     if os.path.exists(extra_jpeg):
        #         os.remove(extra_jpeg)
        #     if os.path.exists(extra_png):
        #         os.remove(extra_png)
        #     continue

        if os.path.islink(extra_jpeg):
            os.remove(extra_jpeg)
        if os.path.islink(extra_png):
            os.remove(extra_png)

        if not os.path.exists(extra_jpeg):
            creations.append((size, original_image, extra_size, extra_jpeg))
        if not os.path.exists(extra_png):
            creations.append((size, original_image, extra_size, extra_png))

    return creations
