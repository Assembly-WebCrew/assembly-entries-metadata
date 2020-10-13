#!/usr/bin/env python3

import argparse
import asmmetadata
import json
import os
import re
import sys

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('metadata_file', type=argparse.FileType("r"))
    args = parser.parse_args(argv[1:])

    metadata = asmmetadata.parse_file(args.metadata_file)

    for section in metadata.sections:
        for entry in section["entries"]:
            if "partyman-id" in entry and "youtube" in entry:
                print("https://www.youtube.com/watch?v=%s" % entry["youtube"], entry["title"], "\t",
                      )

    return os.EX_OK

if __name__ == "__main__":
    sys.exit(main(sys.argv))
