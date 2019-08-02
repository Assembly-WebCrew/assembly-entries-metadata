#!/usr/bin/env python3

import archivethumbnails
import argparse
import asmmetadata
import multiprocessing
import os
import os.path
import subprocess
import sys
import urllib.error
import urllib.request


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

    with open(target + ".tmp%d" % os.getpid(), "wb") as original_image:
        original_image.write(thumbnail_data)
    os.rename(target + ".tmp%d" % os.getpid(), target)
    return target


def main(argv):
    multipliers = [1.25, 1.5, 2, 3, 4]
    size_default = archivethumbnails.ImageSize(160, 90)
    extra_sizes = []
    for multiplier in multipliers:
        extra_sizes.append(
            archivethumbnails.ImageSize(
                int(160 * multiplier),
                int(160 * multiplier * 9 / 16)))

    parser = argparse.ArgumentParser()
    parser.add_argument("datafile")
    parser.add_argument("thumbnail_dir")
    args = parser.parse_args(argv[1:])

    thumbnail_dir = args.thumbnail_dir
    if not os.path.isdir(thumbnail_dir):
        print("Target directory %s does not exist!" % thumbnail_dir)
        return os.EX_DATAERR

    entry_data = asmmetadata.parse_file(open(args.datafile))

    create_thumbnail_calls = []
    for entry in entry_data.entries:
        if 'youtube' not in entry:
            continue
        youtube_id = asmmetadata.get_clean_youtube_id(entry)

        target_orig = os.path.join(thumbnail_dir, "%s-orig.jpeg" % youtube_id)
        target_orig_png = os.path.join(
            thumbnail_dir, "%s-orig.png" % youtube_id)

        # These are "thumbnail missing" images.
        if os.path.islink(target_orig):
            os.remove(target_orig)
        if os.path.islink(target_orig_png):
            os.remove(target_orig_png)

        if not os.path.isfile(target_orig):
            filename = download_thumbnail(youtube_id, target_orig)
            if filename is None:
                link_to_missing_thumbnail("jpeg", target_orig)
                link_to_missing_thumbnail("png", target_orig_png)
        if not os.path.isfile(target_orig_png):
            subprocess.call(['convert', target_orig, target_orig_png])
            archivethumbnails.optimize_png(target_orig_png)

        create_thumbnail_calls.extend(
            archivethumbnails.create_thumbnails_tasks(
                target_orig,
                os.path.join(thumbnail_dir, youtube_id),
                size_default,
                extra_sizes))
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    pool.starmap(
        archivethumbnails.create_thumbnail,
        reversed(sorted(create_thumbnail_calls)))
    return os.EX_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
