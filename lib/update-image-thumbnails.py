#!/usr/bin/env python3

import asmmetadata
import archivethumbnails
import argparse
import logging
import multiprocessing
import os
import os.path
import sys
import typing


def main(argv: typing.List[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile")
    parser.add_argument("dataroot")
    parser.add_argument("thumbnails_dir")
    parser.add_argument("base_width", type=int)
    parser.add_argument("--no-height", action='store_true')
    parser.add_argument("--low-quality", action='store_true')
    parser.add_argument("--face-detect-model", type=str)
    args = parser.parse_args(argv[1:])

    convert_params = []
    if args.low_quality:
        convert_params = [
            "-sampling-factor",
            "4:2:0",
            "-strip",
            "-quality",
            "85",
            "-interlace",
            "JPEG",
            "-colorspace",
            "sRGB"]
    multipliers = [1, 3]
    base_height = None
    if not args.no_height:
        base_height = int(args.base_width * 9 / 16)
    size_default = archivethumbnails.ImageSize(
        args.base_width, base_height, convert_params)
    extra_sizes = []
    for multiplier in multipliers:
        extra_width = int(size_default.x * multiplier)
        extra_height = None
        if not args.no_height:
            extra_height = int(size_default.x * multiplier * 9 / 16)
        extra_sizes.append(
            archivethumbnails.ImageSize(
                extra_width, extra_height, convert_params))

    facedetect_calls = []
    create_thumbnail_calls = []
    entry_data = asmmetadata.parse_file(open(args.datafile))
    for entry in entry_data.entries:
        if not ('webfile' in entry or 'image-file' in entry or 'galleriafi' in entry):
            continue
        filename = entry.get('webfile') or entry.get('image-file')
        galleriafi_entry = entry.get("galleriafi")
        if galleriafi_entry is not None:
            filename = "%s/%s" % (
                asmmetadata.normalize_key(entry['section']['name']),
                asmmetadata.get_galleriafi_filename(galleriafi_entry))
        if filename is None:
            filename = "%s/%s-by-%s.jpeg" % (
                asmmetadata.normalize_key(entry['section']['name']),
                asmmetadata.normalize_key(entry['title']),
                asmmetadata.normalize_key(entry['author']))
        _, baseprefix_r = filename[::-1].split(".", 1)
        baseprefix = baseprefix_r[::-1]
        if not asmmetadata.is_image(filename):
            continue
        filename = os.path.join(args.dataroot, filename)
        prefix = os.path.join(args.dataroot, args.thumbnails_dir, baseprefix)
        if not os.path.isdir(os.path.dirname(prefix)):
            os.makedirs(os.path.dirname(prefix))

        create_thumbnail_calls.extend(
            archivethumbnails.create_thumbnails_tasks(
                filename,
                prefix,
                size_default,
                extra_sizes))
        facedetect_calls.append(filename)

    # Face detection can take 10 GB memory/image. Serialize it and
    # cache the results. Parallelism is not a good idea in here..
    if args.face_detect_model:
        total_images = len(facedetect_calls)
        detector = archivethumbnails.FaceDetector(
            args.face_detect_model)
        for i, filename in enumerate(facedetect_calls, 1):
            print("Face %d/%d: %s" % (i, total_images, filename))
            detector(filename)

    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    pool.starmap(archivethumbnails.create_thumbnail, create_thumbnail_calls)

    return os.EX_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
