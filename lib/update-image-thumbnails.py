#!/usr/bin/env python3

import asmmetadata
import archivethumbnails
import argparse
import os
import os.path
import sys


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile")
    parser.add_argument("dataroot")
    parser.add_argument("thumbnails_dir")
    parser.add_argument("base_width", type=int)
    parser.add_argument("--no-height", action='store_true')
    args = parser.parse_args(argv[1:])

    multipliers = [1.25, 1.5, 2, 3, 4]
    base_height = None
    if not args.no_height:
        base_height = int(args.base_width * 9 / 16)
    size_default = archivethumbnails.ImageSize(
        args.base_width, base_height)
    extra_sizes = []
    for multiplier in multipliers:
        extra_width = int(size_default.x * multiplier)
        extra_height = None
        if not args.no_height:
            extra_height = int(size_default.x * multiplier * 9 / 16)
        extra_sizes.append(
            archivethumbnails.ImageSize(extra_width, extra_height))

    entry_data = asmmetadata.parse_file(open(args.datafile))
    for entry in entry_data.entries:
        section = entry["section"]
        if not ('webfile' in entry or 'image-file' in entry or 'galleriafi' in entry):
            continue
        filename = entry.get('webfile') or entry.get('image-file')
        if filename is None:
            filename = "%s/%s-by-%s.jpeg" % (normalize_key(entry['section']['name']), normalize_key(entry['title']), normalize_key(entry['author']))
        baseprefix, _ = filename.split(".")
        if not asmmetadata.is_image(filename):
            continue
        filename = os.path.join(args.dataroot, filename)
        prefix = os.path.join(args.dataroot, args.thumbnails_dir, baseprefix)
        if not os.path.isdir(os.path.dirname(prefix)):
            os.makedirs(os.path.dirname(prefix))

        archivethumbnails.create_thumbnails(
            filename,
            prefix,
            size_default,
            extra_sizes)

    return os.EX_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
