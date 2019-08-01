#!/usr/bin/env python3

import collections
import os
import os.path
import PIL.Image
import subprocess
import tempfile

ImageSize = collections.namedtuple("ImageSize", ["x", "y"])


def get_image_size(filename):
    image = PIL.Image.open(filename)
    return ImageSize(*image.size)


def optimize_png(source):
    temporary_png = "%s.zpng" % source
    subprocess.check_call(['zopflipng', '-m', source, temporary_png])
    subprocess.check_call(['mv', temporary_png, source])


def create_thumbnail(
        original_image,
        target_file,
        size):
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


def create_thumbnails(
        original_image, target_prefix, default_size, extra_sizes):
    size = get_image_size(original_image)
    default_jpeg = "%s-%dw.jpeg" % (target_prefix, default_size.x)
    if not os.path.exists(default_jpeg):
        create_thumbnail(original_image, default_jpeg, default_size)
    default_png = "%s-%dw.jpeg" % (target_prefix, default_size.x)
    if not os.path.exists(default_png):
        create_thumbnail(original_image, default_png, default_size)

    for extra_size in extra_sizes:
        extra_jpeg = "%s-%dw.jpeg" % (target_prefix, extra_size.x)
        extra_png = "%s-%dw.png" % (target_prefix, extra_size.x)
        if size.x < extra_size.x:
            if os.path.exists(extra_jpeg):
                os.remove(extra_jpeg)
            if os.path.exists(extra_png):
                os.remove(extra_png)
            continue

        if not os.path.exists(extra_jpeg):
            create_thumbnail(original_image, extra_jpeg, extra_size)
        if not os.path.exists(extra_png):
            create_thumbnail(original_image, extra_png, extra_size)
