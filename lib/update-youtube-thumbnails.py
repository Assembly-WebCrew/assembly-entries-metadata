#!/usr/bin/env python
import argparse
import asmmetadata
import os
import os.path
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request


def create_thumbnail(source, width, height, target_jpeg, target_png):
    temporary_resized_fp = tempfile.NamedTemporaryFile(prefix=".youtube-thumbnail-", suffix=".png")
    temporary_resized_image = temporary_resized_fp.name

    subprocess.call(['convert', source, '-resize', '%dx1000' % width, temporary_resized_image])

    if not os.path.exists(target_jpeg):
        subprocess.call(['convert', '-gravity', 'Center', '-crop', '%s+0+0' % target_size, '+repage', temporary_resized_image, target_jpeg])
        subprocess.call(['jpegoptim', '--strip-all', target_jpeg])

    if not os.path.exists(target_png):
        subprocess.call(['convert', '-gravity', 'Center', '-crop', '%s+0+0' % target_size, '+repage', temporary_resized_image, target_png])
        temporary_png = "%s.zpng" % target_png
        subprocess.call(['zopflipng', '-m', target_png, temporary_png])
        subprocess.call(['mv', temporary_png, target_png])


def link_to_missing_thumbnail(target_jpeg, target_png):
    directory = os.path.dirname(target_png)
    parent_directory = os.path.dirname(directory)
    missing_jpeg = os.path.join(parent_directory, "thumbnail-missing.jpeg")
    missing_png = os.path.join(parent_directory, "thumbnail-missing.png")

    if not os.path.isfile(missing_jpeg):
        raise RuntimeError("No file for missing JPEG file (%s)." % missing_jpeg)
    if not os.path.isfile(missing_png):
        raise RuntimeError("No file for missing PNG file (%s)." % missing_png)

    os.symlink("../thumbnail-missing.jpeg", target_jpeg)
    os.symlink("../thumbnail-missing.png", target_png)

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

    target_jpeg = os.path.join(thumbnail_dir, "%s.jpeg" % youtube_id)
    target_png = os.path.join(thumbnail_dir, "%s.png" % youtube_id)

    # These are "thumbnail missing" images.
    if os.path.islink(target_jpeg):
        os.remove(target_jpeg)
    if os.path.islink(target_png):
        os.remove(target_png)

    if os.path.isfile(target_jpeg) and os.path.isfile(target_png):
        continue

    thumbnail_address = "http://i.ytimg.com/vi/%s/0.jpg" % youtube_id

    thumbnail_data = None
    try:
        thumbnail_data_request = urllib.request.urlopen(thumbnail_address)
    except urllib.error.HTTPError as e:
        link_to_missing_thumbnail(target_jpeg, target_png)
        continue

    thumbnail_data = thumbnail_data_request.read()

    temporary_image_fp = tempfile.NamedTemporaryFile(
        prefix=".youtube-thumbnail-", suffix=".jpeg", mode="wb")
    temporary_image_fp.write(thumbnail_data)
    temporary_image_fp.flush()

    temporary_image = temporary_image_fp.name

    create_thumbnail(temporary_image, width, height, target_jpeg, target_png)

    temporary_image_fp.close()
