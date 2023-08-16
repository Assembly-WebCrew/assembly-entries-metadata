#!/usr/bin/env python3

import argparse
import asmmetadata
import http.cookiejar
import json
import logging
import os
import re
import sys
import urllib.request


def fetch_data(auth_token):
    auth_header = ("Authorization", "Token %s" % auth_token)
    playlists_request = urllib.request.Request("https://scene.assembly.org/api/v1/playlist/")
    playlists_request.add_header(*auth_header)
    playlists_result = urllib.request.urlopen(playlists_request)
    playlists = json.loads(playlists_result.read())
    all_playlists = {}
    for playlist in playlists:
        slug = playlist["competition"]["slug"]
        print("Fetching", slug)
        try:
            entries_request = urllib.request.Request(
                "https://scene.assembly.org/api/v1/playlist/%s" % slug)
            entries_request.add_header(*auth_header)
            entries_result = urllib.request.urlopen(entries_request)
            entries = json.loads(entries_result.read())
            all_playlists[slug] = entries
        except urllib.error.HTTPError:
            print("Error fetching")
    print("Fetch done")
    return all_playlists

def fetch_data2(auth_token):
    auth_header = ("Authorization", "Token %s" % auth_token)
    playlists_request = urllib.request.Request("https://scene.assembly.org/api/v1/playlist/")
    playlists_request.add_header(*auth_header)
    playlists_result = urllib.request.urlopen(playlists_request)
    playlists = json.loads(playlists_result.read())
    all_playlists = {}
    for playlist in playlists:
        slug = playlist["competition"]["slug"]
        print("Fetching", slug)
        try:
            entries_request = urllib.request.Request(
                "https://scene.assembly.org/api/v1/competition/%s" % slug)
            entries_request.add_header(*auth_header)
            entries_result = urllib.request.urlopen(entries_request)
            entries = json.loads(entries_result.read())
            all_playlists[slug] = entries
        except urllib.error.HTTPError:
            print("Error fetching")
    print("Fetch done")
    return all_playlists


def update_section_partyman_data(section, partyman_playlist, partyman_competition):
    slug = section.get("partyman-slug")
    print("Updating", slug)
    competition_meta = None
    entries = None
    competition_meta = partyman_playlist["competition"]
    entries = partyman_playlist["entries"]
    if entries is None:
        raise RuntimeError("Missing partyman data for slug %r" % slug)

    extradata = {}
    if partyman_competition is not None:
        for c_entry in partyman_competition["entries"]:
            extradata[c_entry.get('uuid')] = c_entry

    section_entries = []
    for partyman_entry in entries:
        entry_entry = partyman_entry["entry"]
        existing_data = None
        for metadata_entry in section['entries']:
            try:
                uuid = int(metadata_entry.get('partyman-id'))
            except:
                uuid = metadata_entry.get('partyman-id')
            if (partyman_entry['pk'] == uuid or entry_entry["uuid"] == uuid):
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

        if entry_entry['uuid'] in extradata:
            extra = extradata[entry_entry.get('uuid')]
            if extra is not None and extra.get('preview_url') is not None:
                addable_data['youtube'] = extra.get('preview_url')[17:]

        slide_info_list = []
        if "slide_text" in entry_entry and entry_entry.get("slide_text") is not None:
            slide_info_list.append(entry_entry.get("slide_text"))
        if "techniques" in entry_entry:
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
        if "screenshot" in entry_entry and entry_entry['screenshot'] is not None:
            base = os.path.basename(entry_entry['screenshot'])
            fn = slug + "/" + base
            target = "../scratch/assembly-2023/" + fn
            if not os.path.exists(target):
                os.makedirs(os.path.dirname(target), 0o700, True)
                urllib.request.urlretrieve("https://scene.assembly.org/" + entry_entry['screenshot'], target)
            addable_data['image-file'] = fn
        # preview_youtube_url = partyman_entry.get("preview", "")
        # youtube_id = None
        # if preview_youtube_url:
        #     youtube_id = asmyoutube.get_video_id_try_url(preview_youtube_url)
        # if youtube_id:
        #     addable_data["youtube"] = youtube_id
        section_entries.append(addable_data)
    section["entries"] = section_entries
    return section


def fetch_update_data(metadata_file, api_token: str):
    playlists = fetch_data(api_token)
    competitions = fetch_data2(api_token)
    metadata = asmmetadata.parse_file(metadata_file)

    metadata_partyman_slugs = []
    for section in metadata.sections:
        print("Processing ", section)
        slug = section.get("partyman-slug")
        print("Slug ", slug)
        if slug is None:
            continue
        if slug not in playlists:
            continue
        #if slug not in competitions:
        #    continue
        cc = None
        if slug in competitions:
            cc = competitions[slug]
        update_section_partyman_data(section, playlists[slug], cc)

    with open(metadata_file.name, "w") as fp:
        asmmetadata.print_metadata(fp, metadata)


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
