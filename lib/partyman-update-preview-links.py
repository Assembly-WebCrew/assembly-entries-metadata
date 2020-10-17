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
        url="https://scene.assembly.org/api/v1/entry/?format=json",
        cookies = cookie_jar)
    entries = result.json()
    return entries


def update_entry_preview_link(cookie_jar, partyman_entry, preview_link):
    if partyman_entry["preview_url"] == preview_link:
        return
    session = requests.Session()
    print("Updating %s by %s" % (partyman_entry["title"], partyman_entry["by"]))
    entry_detail_url = partyman_entry["url"].replace("http://shader", "https://scene").replace("api/v1", "admin") + "detail/"
    result = session.get(url=entry_detail_url, cookies = cookie_jar)
    # print(result.ok)

    requests.utils.add_dict_to_cookiejar(cookie_jar, requests.utils.dict_from_cookiejar(result.cookies))
    entry_api_url = partyman_entry["url"].replace("http://shader", "https://scene")
    csrf_token = requests.utils.dict_from_cookiejar(result.cookies)["csrftoken"]
    response = session.patch(
        url = entry_api_url,
        headers = {"X-CSRFToken": csrf_token},
        data = {"preview_url": preview_link},
        cookies = cookie_jar)
    if not response.ok:
        print(response.text)
    # opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    # opener.method = "PATCH"
    # data_string = "preview_link=%s" % 
    # result = opener.open(, data=data_string.encode("utf-8"))
    # result.read()
    #request_entry = opener.open("https://scene.assembly.org/api/v1/entry/?format=json")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('metadata_file', type=argparse.FileType("r"))
    parser.add_argument('cookie_jar')
    parser.add_argument('--section')
    args = parser.parse_args(argv[1:])

    cookie_jar = http.cookiejar.MozillaCookieJar(args.cookie_jar)
    cookie_jar.load()
    partyman_entries = fetch_partyman_data(cookie_jar)
    metadata = asmmetadata.parse_file(args.metadata_file)

    entries_by_uuid = {}
    for entry_id, entry in enumerate(partyman_entries):
        entry["id"] = entry_id
        entries_by_uuid[entry["uuid"]] = entry

    for section in metadata.sections:
        if args.section is not None:
            if asmmetadata.normalize_key(section["name"]) != args.section:
                continue
        for entry in section["entries"]:
            if "partyman-id" not in entry:
                continue
            partyman_entry = entries_by_uuid[entry["partyman-id"]]
            preview_link = None
            if "youtube" in entry:
                preview_link = "https://www.youtube.com/watch?v=%s" % entry["youtube"]
            if 'image-file' in entry:
                preview_link = asmmetadata.get_archive_link_entry(entry)
            if preview_link is None:
                continue
            update_entry_preview_link(cookie_jar, partyman_entry, preview_link)
    return os.EX_OK

if __name__ == "__main__":
    sys.exit(main(sys.argv))
