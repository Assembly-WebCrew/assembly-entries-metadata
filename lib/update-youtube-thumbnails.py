#!/usr/bin/env python3

import argparse
import asmmetadata
import collections
import os
import os.path
import PIL.Image
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request


ImageSize = collections.namedtuple("ImageSize", ["x", "y"])


def get_image_size(filename):
    image = PIL.Image.open(filename)
    return ImageSize(*image.size)


def convert_to_png(source, target):
    subprocess.call(['convert', source, target])
    temporary_png = "%s.zpng" % target
    subprocess.call(['zopflipng', '-m', target, temporary_png])
    subprocess.call(['mv', temporary_png, target_png])


def create_thumbnail(source, width, height, target_jpeg, target_png):
    temporary_resized_fp = tempfile.NamedTemporaryFile(
        prefix=".youtube-thumbnail-", suffix=".png")
    temporary_resized_image = temporary_resized_fp.name

    subprocess.call(
        ['convert', source, '-resize', '%dx100000' % width,
         temporary_resized_image])

    if not os.path.exists(target_jpeg):
        subprocess.call(
            ['convert', '-gravity', 'Center', '-crop', '%s+0+0' % target_size,
             '+repage', temporary_resized_image, target_jpeg])
        subprocess.call(['jpegoptim', '--strip-all', target_jpeg])

    if not os.path.exists(target_png):
        subprocess.call(
            ['convert', '-gravity', 'Center', '-crop', '%s+0+0' % target_size,
             '+repage', temporary_resized_image, target_png])
        convert_to_png(temporary_resized_image, target_png)


def link_to_missing_thumbnail(missing_type, target):
    missing_filename = "../thumbnail-missing.%s" % missing_type
    target_dir = os.path.dirname(target)

    missing_path = os.path.join(target_dir, missing_filename)
    if not os.path.isfile(missing_path):
        raise RuntimeError(
            "No file for missing file (%s)." % missing_path)
    if os.path.exists(target) and os.readlink(target) == missing_filename:
        return

    os.symlink(missing_filename, target)


def download_thumbnail(youtube_id, target):
    thumbnail_address = "http://i.ytimg.com/vi/%s/0.jpg" % youtube_id

    thumbnail_data = None
    try:
        thumbnail_data_request = urllib.request.urlopen(thumbnail_address)
    except urllib.error.HTTPError:
        return None

    thumbnail_data = thumbnail_data_request.read()

    with open(target_orig + ".tmp%d" % os.getpid(), "wb") as original_image:
        original_image.write(thumbnail_data)
    os.rename(target_orig + ".tmp%d" % os.getpid(), target_orig)
    return target_orig


parser = argparse.ArgumentParser()
parser.add_argument("thumbnail_dir")
parser.add_argument("width", type=int)
parser.add_argument("height", type=int)
args = parser.parse_args()

thumbnail_dir = args.thumbnail_dir
if not os.path.isdir(thumbnail_dir):
    print("Target directory %s does not exist!" % thumbnail_dir)
    sys.exit(1)
width = args.width
height = args.height
target_size = "%dx%d" % (width, height)

entry_data = asmmetadata.parse_file(sys.stdin)

for entry in entry_data.entries:
    if 'youtube' not in entry:
        continue
    youtube_id = asmmetadata.get_clean_youtube_id(entry)

    target_jpeg = os.path.join(
        thumbnail_dir, "%s-%dw.jpeg" % (youtube_id, width))
    target_png = os.path.join(
        thumbnail_dir, "%s-%dw.png" % (youtube_id, width))

    target_orig = os.path.join(thumbnail_dir, "%s-orig.jpeg" % youtube_id)
    target_orig_png = os.path.join(thumbnail_dir, "%s-orig.png" % youtube_id)
    if not os.path.isfile(target_orig):
        filename = download_thumbnail(youtube_id, target_orig)
        if filename is None:
            link_to_missing_thumbnail("jpeg", target_jpeg)
            link_to_missing_thumbnail("png", target_png)
            continue
    else:
        if not os.path.isfile(target_orig_png):
            convert_to_png(target_orig, target_orig_png)

    size = get_image_size(target_orig)
    if size.x < args.width and size.y < args.height:
        os.remove(target_jpeg)
        os.remove(target_png)
        os.symlink(target_jpeg, target_jpeg)
        os.symlink(target_png, target_png)
        continue

    # These are "thumbnail missing" images.
    if os.path.islink(target_jpeg):
        os.remove(target_jpeg)
    if os.path.islink(target_png):
        os.remove(target_png)

    if os.path.isfile(target_jpeg) and os.path.isfile(target_png):
        continue

    create_thumbnail(target_orig, width, height, target_jpeg, target_png)
