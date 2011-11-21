#!/usr/bin/env python
import asmmetadata
import os
import os.path
import subprocess
import sys
import tempfile

temporary_image_fp = tempfile.NamedTemporaryFile(prefix=".youtube-thumbnail-", suffix=".jpeg")
temporary_image = temporary_image_fp.name
temporary_resized_fp = tempfile.NamedTemporaryFile(prefix=".youtube-thumbnail-", suffix=".png")
temporary_resized_image = temporary_resized_fp.name

if len(sys.argv) != 4:
    print "Usage: %s thumbnail_dir width height" % sys.argv[0]
    sys.exit(1)

thumbnail_dir = sys.argv[1]
if not os.path.exists(thumbnail_dir):
    print "Target directory %s does not exist!" % thumbnail_dir
    sys.exit(1)
width = int(sys.argv[2])
height = int(sys.argv[3])
target_size = "%dx%d" % (width, height)

entry_data = asmmetadata.parse_file(sys.stdin)

for entry in entry_data.entries:
    if 'youtube' not in entry:
        continue
    youtube_id = entry['youtube']

    target_jpeg = os.path.join(thumbnail_dir, "%s.jpeg" % youtube_id)
    target_png = os.path.join(thumbnail_dir, "%s.png" % youtube_id)
    if os.path.exists(target_jpeg) and os.path.exists(target_png):
        continue

    thumbnail_address = "http://i.ytimg.com/vi/%s/0.jpg" % youtube_id

    subprocess.call(['wget', '-O', temporary_image, thumbnail_address])
    subprocess.call(['convert', temporary_image, '-resize', '%dx1000' % width, temporary_resized_image])
    os.remove(temporary_image)

    if not os.path.exists(target_jpeg):
        subprocess.call(['convert', '-gravity', 'Center', '-crop', '%s+0+0' % target_size, '+repage', temporary_resized_image, target_jpeg])
        subprocess.call(['jpegoptim', '--strip-all', target_jpeg])

    if not os.path.exists(target_png):
        subprocess.call(['convert', '-gravity', 'Center', '-crop', '%s+0+0' % target_size, '+repage', temporary_resized_image, target_png])
        subprocess.call(['optipng', '-o7', target_png])

    os.remove(temporary_resized_image)
