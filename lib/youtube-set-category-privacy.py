#!/usr/bin/env python

import asmmetadata
import asmyoutube
import argparse


def set_playlist_privacy(privacy, yt_service, section):
    if "youtube-playlist" not in section:
        return
    playlist_list = asmyoutube.try_operation(
        "playlist %s" % section["name"],
        lambda: yt_service.playlists().list(
            id=section["youtube-playlist"],
            part="snippet,status"
        ).execute(),
        sleep=1)
    if not playlist_list["items"]:
        print("No playlist found for ID %s" % section["youtube-playlist"])
        return
    playlist_status = playlist_list["items"][0]["status"]
    if playlist_status["privacyStatus"] == privacy:
        return

    # Snippet is always required for playlist updates:
    playlist_snippet = playlist_list["items"][0]["snippet"]
    playlist_status["privacyStatus"] = privacy
    asmyoutube.try_operation(
        "update playlist privacy %s" % section["name"],
        lambda: yt_service.playlists().update(
            part="snippet,status",
            body=dict(
                snippet=playlist_snippet,
                status=playlist_status,
                id=section["youtube-playlist"])).execute(),
        sleep=1)


def set_section_privacy(privacy, yt_service, section):
    set_playlist_privacy(privacy, yt_service, section)

    for entry in section["entries"]:
        if "youtube" not in entry:
            continue
        videos_list = asmyoutube.try_operation(
            "get %s" % entry['title'],
            lambda: yt_service.videos().list(
                id=asmmetadata.get_clean_youtube_id(entry),
                part="status"
                ).execute(),
            sleep=1)

        if not videos_list["items"]:
            print("No video found for ID %s" % entry["youtube"])
            continue

        video_status = videos_list["items"][0]["status"]

        if video_status["privacyStatus"] == privacy:
            continue

        video_status["privacyStatus"] = privacy
        asmyoutube.try_operation(
            "update privacy %s" % entry['title'],
            lambda: yt_service.videos().update(
                part="status",
                body=dict(
                    status=video_status,
                    id=asmmetadata.get_clean_youtube_id(entry))).execute(),
            sleep=1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile")
    parser.add_argument("sections")
    parser.add_argument(
        "privacy", choices=["public", "private", "unlisted"])
    asmyoutube.add_auth_args(parser)
    args = parser.parse_args()
    yt_service = asmyoutube.get_authenticated_service(args)
    entry_data = asmmetadata.parse_file(open(args.datafile, "rb"))

    sections = [x.strip() for x in args.sections.split(",")]
    for section in entry_data.sections:
        if section["key"] not in sections:
            continue
        set_section_privacy(args.privacy, yt_service, section)
