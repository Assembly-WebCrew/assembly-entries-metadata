#!/usr/bin/env python3

import argparse
import asmmetadata
import json
import os
import re
import sys

def update_section_partyman_data(section, partyman_competitions):
    slug = section.get("partyman-slug")
    competition_meta = None
    entries = None
    for partyman_competition in partyman_competitions:
        if partyman_competition["competition"]["slug"] == slug:
            competition_meta = partyman_competition["competition"]
            entries = partyman_competition["entries"]
            break
    if entries is None:
        raise RuntimeError("Missing partyman data for slug %r" % slug)

    section_entries = []
    for partyman_entry in entries:
        existing_data = None
        for metadata_entry in section['entries']:
            if partyman_entry['pk'] == int(metadata_entry.get('partyman-id')):
                existing_data = metadata_entry
                break
        addable_data = existing_data
        if existing_data is None:
            addable_data = {'section': section}
        addable_data['partyman-id'] = partyman_entry['pk']
        title = partyman_entry["entry"]['title']
        title = title.replace("|", "-")
        addable_data['title'] = title
        author = partyman_entry["entry"].get("by")
        if not author:
            author = "author-will-be-revealed-after-compo"
        author = author.replace("|", "-")
        addable_data['author'] = author
        slide_info = partyman_entry["entry"].get("slide_info")
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
    # https://scene.assembly.org/api/v1/entry/
    # https://scene.assembly.org/api/v1/playlist/
    parser.add_argument("partyman_playlist", type=argparse.FileType("r"))
    args = parser.parse_args(argv[1:])

    metadata = asmmetadata.parse_file(args.metadata_file)
    partyman_data = json.load(args.partyman_playlist)

    metadata_partyman_slugs = []
    for section in metadata.sections:
        slug = section.get("partyman-slug")
        if slug is None:
            continue
        update_section_partyman_data(section, partyman_data)

    with open(args.metadata_file.name, "w") as fp:
        asmmetadata.print_metadata(fp, metadata)
    return os.EX_OK

if __name__ == "__main__":
    sys.exit(main(sys.argv))
