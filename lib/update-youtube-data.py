import asmmetadata
import argparse
import os
import sys
import asmyoutube


def update_youtube_info(yt_service, entry_data):
    for entry in entry_data.entries:
        if 'youtube' not in entry:
            continue
        if not entry["section"]["manage-youtube-descriptions"]:
            continue
        update_youtube_info_entry(yt_service, entry)


def update_youtube_info_entry(yt_service, entry):
    youtube_info = asmmetadata.get_youtube_info_data(entry)

    videos_list = asmyoutube.try_operation(
        "get info for %s" % youtube_info['title'],
        lambda: yt_service.videos().list(
            id=entry["youtube"], part="snippet").execute(),
        sleep=1)
    if not videos_list["items"]:
        print("No video found for ID %s" % entry["youtube"])
        return

    video_item = videos_list["items"][0]
    video_snippet = video_item["snippet"]

    update_entry = False
    if video_snippet["title"] != youtube_info["title"]:
        update_entry = True
        video_snippet["title"] = youtube_info["title"]
    if video_snippet["description"] != youtube_info['description'].strip():
        update_entry = True
        video_snippet["description"] = youtube_info['description'].strip()
    existing_tags = []
    if video_snippet.get("tags"):
        existing_tags = sorted(
            [tag.strip().lower() for tag in video_snippet["tags"]])
    if existing_tags != sorted(
            [tag.strip().lower() for tag in youtube_info["tags"]]):
        update_entry = True
        video_snippet["tags"] = youtube_info["tags"]

    if update_entry:
        asmyoutube.try_operation(
            "update %s" % youtube_info['title'],
            lambda: yt_service.videos().update(
                part="snippet",
                body=dict(
                    id=entry["youtube"],
                    snippet=video_snippet)).execute())


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile")
    parser.add_argument("--sections", default="")
    asmyoutube.add_auth_args(parser)
    args = parser.parse_args(argv[1:])
    yt_service = asmyoutube.get_authenticated_service(args)

    entry_data = asmmetadata.parse_file(open(args.datafile, "rb"))

    if args.sections:
        included_sections = set(
            [x.lower().strip() for x in args.sections.split(",")])
        included_entries = []
        for entry in entry_data.entries:
            if entry["section"]["key"] in included_sections:
                included_entries.append(entry)
        entry_data.entries = included_entries

    try:
        update_youtube_info(yt_service, entry_data)
    except KeyboardInterrupt:
        print "Interrupted"
        return os.EX_DATAERR

    return os.EX_OK

if __name__ == "__main__":
    sys.exit(main(sys.argv))
