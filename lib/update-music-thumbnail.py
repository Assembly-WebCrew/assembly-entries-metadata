#!/usr/bin/env python3

import archivethumbnails
import argparse
import multiprocessing
import os
import os.path
import sys


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("background_file")
    parser.add_argument("thumbnails_dir")
    args = parser.parse_args(argv[1:])

    base_width = 160

    multipliers = [1.25, 1.5, 2, 3, 4]
    base_height = int(base_width * 9 / 16)
    size_default = archivethumbnails.ImageSize(
        base_width, base_height)
    extra_sizes = []
    for multiplier in multipliers:
        extra_width = int(size_default.x * multiplier)
        extra_height = int(size_default.x * multiplier * 9 / 16)
        extra_sizes.append(
            archivethumbnails.ImageSize(extra_width, extra_height))

    filename = args.background_file
    out_prefix = os.path.join(args.thumbnails_dir, "music-thumbnail")
    create_thumbnail_calls = archivethumbnails.create_thumbnails_tasks(
        filename, out_prefix, size_default, extra_sizes)
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    pool.starmap(archivethumbnails.create_thumbnail, create_thumbnail_calls)
    return os.EX_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
