#!/usr/bin/env python3

import collections
import logging
import os
import os.path
import PIL.Image
import PIL.ImageFile
import subprocess
import tempfile

ImageSize = collections.namedtuple("ImageSize", ["x", "y"])
# Disable decompression bomb protection. This is required to process
# some PNG images with PIL...
PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True


def get_image_size(filename):
    try:
        image = PIL.Image.open(filename)
    except Exception as e:
        logging.error("Unable to open %s: %s", filename, e)
        raise e
    return ImageSize(*image.size)


def optimize_png(source):
    temporary_png = "%s.zpng" % source
    subprocess.check_call(['zopflipng', '-m', '-y', source, temporary_png])
    subprocess.check_call(['mv', temporary_png, source])


def create_thumbnail(
        size,
        original_image,
        target_file):
    if os.path.exists(target_file):
        return
    temporary_resized_fp = tempfile.NamedTemporaryFile(
        prefix=".thumbnail-", suffix=".png")
    temporary_resized_image = temporary_resized_fp.name

    subprocess.check_call(
        ['convert', original_image, '-resize', '%dx20000' % size.x,
         temporary_resized_image])

    if size.y is not None:
        target_size = "%dx%d" % (size.x, size.y)
        subprocess.check_call(
            ['convert', '-gravity', 'Center', '-crop', '%s+0+0' % target_size,
             '+repage', temporary_resized_image, target_file])
    else:
        subprocess.check_call(
            ["convert", temporary_resized_image, target_file])

    if target_file.endswith(".jpeg"):
        subprocess.check_call(['jpegoptim', '--strip-all', target_file])
    if target_file.endswith(".png"):
        optimize_png(target_file)


def create_thumbnails_tasks(
        original_image, target_prefix, default_size, extra_sizes):
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
