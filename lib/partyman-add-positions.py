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

def fetch_data(auth_token):
    auth_header = ("Authorization", "Token %s" % auth_token)
    results_request = urllib.request.Request("https://scene.assembly.org/api/v1/results/")
    results_request.add_header(*auth_header)
    results_result = urllib.request.urlopen(results_request)
    results = json.loads(results_result.read())
    all_results = {}
    for section_result in results:
        slug = section_result["competition"]["slug"]
        entries_request = urllib.request.Request(
            "https://scene.assembly.org/api/v1/results/%s" % slug)
        entries_request.add_header(*auth_header)
        entries_result = urllib.request.urlopen(entries_request)
        entries = json.loads(entries_result.read())
        all_results[slug] = entries
    return all_results


def fetch_update_data(metadata_file, api_token: str):
    results = fetch_data(api_token)
    metadata = asmmetadata.parse_file(metadata_file)

    metadata_partyman_slugs = []
    for section in metadata.sections:
        slug = section.get("partyman-slug")
        if slug is None:
            continue
        if slug not in results:
            continue
        update_section_partyman_data(section, results[slug])

    with open(metadata_file.name, "w") as fp:
        asmmetadata.print_metadata(fp, metadata)


def update_section_partyman_data(section, partyman_results):
    slug = section.get("partyman-slug")
    competition_meta = None
    entries = None
    competition_meta = partyman_results["competition"]
    entries = partyman_results["entries"]
    if entries is None:
        raise RuntimeError("Missing partyman data for slug %r" % slug)

    section_entries = []
    for partyman_entry in entries:
        entry_entry = partyman_entry["entry"]
        existing_data = None
        for metadata_entry in section['entries']:
            try:
                uuid = int(metadata_entry.get('partyman-id'))
            except:
                uuid = metadata_entry.get('partyman-id')
            if entry_entry["uuid"] == uuid:
                existing_data = metadata_entry
                break
        addable_data = existing_data
        if existing_data is None:
            addable_data = {'section': section}
        addable_data['partyman-id'] = entry_entry['uuid']
        title = entry_entry['title']
        title = title.replace("|", "-")
        addable_data['title'] = title
        author = entry_entry.get("by")
        if not author:
            author = "author-will-be-revealed-after-compo"
        author = author.replace("|", "-")
        addable_data['author'] = author
        slide_info_list = []
        if "slide_text" in entry_entry and entry_entry['slide_text'] is not None:
            slide_info_list.append(entry_entry.get("slide_text"))
        if "techniques" in entry_entry and entry_entry['techniques'] is not None:
            slide_info_list.append(entry_entry.get("techniques"))
        slide_info = "\n".join(slide_info_list)
        if slide_info:
             slide_info = slide_info.strip()
             slide_info = slide_info.replace("&", "&amp;")
             slide_info = slide_info.replace("<", "&lt;")
             slide_info = slide_info.replace("\r", "")
             slide_info = re.sub("\n+", "\n", slide_info)
             slide_info = slide_info.replace("\n", "<br/>")
             slide_info = slide_info.replace("|", "-")
             addable_data["techniques"] = slide_info
        elif "techniques" in addable_data:
            del addable_data["techniques"]
        addable_data["position"] = partyman_entry["rank"]
        # preview_youtube_url = partyman_entry.get("preview", "")
        # youtube_id = None
        # if preview_youtube_url:
        #     youtube_id = asmyoutube.get_video_id_try_url(preview_youtube_url)
        # if youtube_id:
        #     addable_data["youtube"] = youtube_id
        section_entries.append(addable_data)
    section["entries"] = section_entries
    return section


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('metadata_file', type=argparse.FileType("r"))

    partyman_api_token = os.getenv("PARTYMAN_API_TOKEN", None)
    if not partyman_api_token:
        logging.error("""\
PARTYMAN_API_TOKEN environment variable should be set with an \
appropriate Partyman API Token value!""")
        return os.EX_DATAERR
    args = parser.parse_args(argv[1:])
    fetch_update_data(args.metadata_file, partyman_api_token)
    return os.EX_OK

if __name__ == "__main__":
    sys.exit(main(sys.argv))
