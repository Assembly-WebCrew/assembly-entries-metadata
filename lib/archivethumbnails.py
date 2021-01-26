#!/usr/bin/env python3

import collections
import dataclasses
import dlib  # type: ignore
import logging
import os
import os.path
import PIL.Image  # type: ignore
import PIL.ImageFile  # type: ignore
import subprocess
import tempfile
import typing

ImageSize = collections.namedtuple(
    "ImageSize", ["x", "y", "extra_convert_params"])
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
    subprocess.check_call(['zopflipng', '-m', '-y', source, temporary_png])
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


class FaceDetector:
    def __init__(self, datafile: str):
        self.algorithm = "dlib.cnn_face_detection_model_v1"
        self.data_id = os.path.basename(datafile)
        self.detector = dlib.cnn_face_detection_model_v1(datafile)

    def __call__(self, original_image: str) -> FaceDetectData:
        face_detect_file = original_image + ".faces.txt"
        face_detect_data = load_face_detect_data(face_detect_file)
        if face_detect_data is not None:
            return face_detect_data

        image = dlib.load_rgb_image(original_image)
        width, height, _ = image.shape
        detections = self.detector(image, 1)

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
            fd_parameters="upscales=1",
            image_width=width,
            image_height=height,
            faces=faces,
        )

        save_face_detect_data(face_detect_file, face_detect_data)
        return face_detect_data


def create_thumbnail(
        size: ImageSize,
        original_image: str,
        target_file: str) -> None:
    if os.path.exists(target_file):
        return
    temporary_resized_fp = tempfile.NamedTemporaryFile(
        prefix=".thumbnail-", suffix=".png")
    temporary_resized_image = temporary_resized_fp.name

    subprocess.check_call(
        ['convert', original_image, '-resize', '%dx20000' % size.x,
         temporary_resized_image])

    # XXX hack
    convert_params = []
    if target_file.endswith(".jpeg"):
        convert_params = size.extra_convert_params
    if size.y is not None:
        target_size = "%dx%d" % (size.x, size.y)
        convert_call = [
            'convert',
            '-gravity',
            'Center',
            '-crop',
            '%s+0+0' % target_size,
            '+repage'] + convert_params
        subprocess.check_call(
            convert_call + [temporary_resized_image, target_file])
    else:
        subprocess.check_call(
            (["convert"]
             + convert_params
             + [temporary_resized_image, target_file]))

    if target_file.endswith(".jpeg"):
        subprocess.check_call(['jpegoptim', '--strip-all', target_file])
    if target_file.endswith(".png"):
        optimize_png(target_file)


def create_thumbnails_tasks(
        original_image: str,
        target_prefix: str,
        default_size: ImageSize,
        extra_sizes: typing.List[ImageSize]):
    creations = []
    size = get_image_size(original_image)
    default_jpeg = "%s-%dw.jpeg" % (target_prefix, default_size.x)
    if not os.path.exists(default_jpeg):
        creations.append((default_size, original_image, default_jpeg))
    default_png = "%s-%dw.png" % (target_prefix, default_size.x)
    if not os.path.exists(default_png):
        creations.append((default_size, original_image, default_png))

    for extra_size in extra_sizes:
        extra_jpeg = "%s-%dw.jpeg" % (target_prefix, extra_size.x)
        extra_png = "%s-%dw.png" % (target_prefix, extra_size.x)
        if size.x < extra_size.x:
            if os.path.exists(extra_jpeg):
                os.remove(extra_jpeg)
            if os.path.exists(extra_png):
                os.remove(extra_png)
            continue

        if os.path.islink(extra_jpeg):
            os.remove(extra_jpeg)
        if os.path.islink(extra_png):
            os.remove(extra_png)

        if not os.path.exists(extra_jpeg):
            creations.append((extra_size, original_image, extra_jpeg))
        if not os.path.exists(extra_png):
            creations.append((extra_size, original_image, extra_png))

    return creations
