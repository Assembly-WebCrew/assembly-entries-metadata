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


def fetch_partyman_data(cookie_jar):
    result = requests.get(
        url="https://scene.assembly.org/api/v0/entry/?format=json",
        cookies = cookie_jar)
    entries = result.json()
    return entries


def update_entry_preview_link(
        partyman_api_token: str,
        entry: asmmetadata.Entry,
        preview_link: str):
    session = requests.Session()
    print("Updating %s" % asmmetadata.get_entry_name(entry))
    entry_api_url = "https://scene.assembly.org/api/v1/entry/%s/" % entry["partyman-id"]
    response = session.patch(
        url = entry_api_url,
        headers = {"Authorization": "Token %s" % partyman_api_token},
        data = {"preview_url": preview_link})
    if not response.ok:
        print(response.text)
    # opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    # opener.method = "PATCH"
    # data_string = "preview_link=%s" % 
    # result = opener.open(, data=data_string.encode("utf-8"))
    # result.read()
    #request_entry = opener.open("https://scene.assembly.org/api/v0/entry/?format=json")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('metadata_file', type=argparse.FileType("r"))
    parser.add_argument('--section', required=True)
    partyman_api_token = os.getenv("PARTYMAN_API_TOKEN", None)
    if not partyman_api_token:
        logging.error("""\
PARTYMAN_API_TOKEN environment variable should be set with an \
appropriate Partyman API Token value!""")
        return os.EX_DATAERR
    args = parser.parse_args(argv[1:])

    metadata = asmmetadata.parse_file(args.metadata_file)

    for section in metadata.sections:
        if args.section is not None:
            if asmmetadata.normalize_key(section["name"]) != args.section:
                continue
        for entry in section["entries"]:
            if "partyman-id" not in entry:
                continue
            preview_link = None
            if "youtube" in entry:
                preview_link = "https://www.youtube.com/watch?v=%s" % entry["youtube"]
            if 'image-file' in entry:
                preview_link = asmmetadata.get_archive_link_entry(entry)
            if preview_link is None:
                continue
            update_entry_preview_link(partyman_api_token, entry, preview_link)
    return os.EX_OK

if __name__ == "__main__":
    sys.exit(main(sys.argv))
