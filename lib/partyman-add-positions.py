#!/usr/bin/env python3

import argparse
import asmmetadata
import http.cookiejar
import json
import os
import re
import requests
import requests.utils
import sys
import urllib.request

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('metadata_file', type=argparse.FileType("r"))
    parser.add_argument('cookie_jar')
    args = parser.parse_args(argv[1:])

    metadata = asmmetadata.parse_file(args.metadata_file)

    cookie_jar = http.cookiejar.MozillaCookieJar(args.cookie_jar)
    cookie_jar.load()
    results_response = requests.get(
        url="https://scene.assembly.org/api/v1/results/?format=json",
        cookies = cookie_jar)
    partyman_results = results_response.json()
    result_by_uuid = {}
    for competition in partyman_results:
        for position, entry in enumerate(competition["entries"], 1):
            entry["position"] = position
            result_by_uuid[entry["entry"]["uuid"]] = entry

    for entry in metadata.entries:
        if "partyman-id" not in entry:
            continue
        partyman_entry = result_by_uuid[entry["partyman-id"]]
        entry["position"] = partyman_entry["position"]
        # Reveal authors.
        entry["author"] = partyman_entry["entry"]["by"]
    for section in metadata.sections:
        asmmetadata.reorder_positioned_section_entries(section['entries'])

    with open(args.metadata_file.name, "w") as fp:
        asmmetadata.print_metadata(fp, metadata)
    return os.EX_OK

if __name__ == "__main__":
    sys.exit(main(sys.argv))
