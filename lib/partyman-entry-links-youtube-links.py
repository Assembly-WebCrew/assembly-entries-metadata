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
    parser.add_argument('partyman_entry_file', type=argparse.FileType("r"))
    args = parser.parse_args(argv[1:])

    metadata = asmmetadata.parse_file(args.metadata_file)
    partyman_entries = json.load(args.partyman_entry_file)
    entries_by_uuid = {}
    for entry_id, entry in enumerate(partyman_entries):
        entry["id"] = entry_id
        entries_by_uuid[entry["uuid"]] = entry

    for section in metadata.sections:
        print(section["name"])
        for entry in section["entries"]:
            if "partyman-id" in entry and "youtube" in entry:
                partyman_entry = entries_by_uuid[entry["partyman-id"]]
                print(
                    partyman_entry["url"].replace("http://shader", "https://scene").replace("api/v1", "admin") + "detail/", "\t",
                    "https://www.youtube.com/watch?v=%s" % entry["youtube"], entry["title"])
        print()
    return os.EX_OK

if __name__ == "__main__":
    sys.exit(main(sys.argv))
