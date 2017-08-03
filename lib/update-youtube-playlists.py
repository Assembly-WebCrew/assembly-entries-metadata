import argparse
import asmmetadata
import asmyoutube
import os
import re
import sys
import time
import urlparse


def has_youtube_entries(section):
    for entry in section['entries']:
        if 'youtube' in entry:
            return True
    return False


def get_playlist_title(section):
    return u"%s %s" % (
        asmmetadata.get_party_name(section["year"], section['name']),
        asmmetadata.get_long_section_name(section))


def get_playlist_description(section):
    playlist_description = section.get('description', u'')
    playlist_description = re.sub("</p><p>", "\n\n", playlist_description)
    playlist_description = re.sub("<[^>]+>", "", playlist_description)
    return playlist_description


def create_playlist(yt_service, entry_data, section):
    playlist_title = get_playlist_title(section)
    playlist_description = get_playlist_description(section)

    new_playlist = yt_service.playlists().insert(
        part="snippet,status",
        body=dict(
            snippet=dict(
                title=playlist_title,
                description=playlist_description
                ),
            status=dict(
                privacyStatus="public"
                )
            )
        ).execute()
    return new_playlist["id"]


def get_playlist(yt_service, section):
    playlist_id = section['youtube-playlist']
    playlists = yt_service.playlists().list(
        part="snippet", id=playlist_id).execute()
    if not playlists["items"]:
        return None
    return playlists["items"][0]


def fetch_youtube_playlist_entries(yt_service, section):
    all_videos = []
    next_page_token = ""
    for _ in range(10):
        new_videos = yt_service.playlistItems().list(
            part="snippet",
            playlistId=section["youtube-playlist"],
            maxResults=50,
            pageToken=next_page_token).execute()
        if not new_videos["items"]:
            return all_videos
        all_videos.extend(new_videos["items"])
        if len(new_videos["items"]) < 50:
            return all_videos
        next_page_token = new_videos["nextPageToken"]
    # We probably shouldn't have over 500 videos on one playlist...
    return all_videos


def modify_youtube_playlist(yt_service, playlist, section):
    playlist_snippet = playlist["snippet"]
    update = False
    playlist_title = get_playlist_title(section)
    if playlist_snippet["title"] != playlist_title:
        update = True
        playlist_snippet["title"] = playlist_title
    playlist_description = get_playlist_description(section)
    if playlist_snippet["description"] != playlist_description:
        update = True
        playlist_snippet["description"] = playlist_description

    if not update:
        return
    asmyoutube.try_operation(
        "Update playlist metadata",
        lambda: yt_service.playlists().update(
            part="snippet",
            body=dict(
                snippet=playlist_snippet,
                id=section["youtube-playlist"])).execute())


def update_youtube_playlists(yt_service, entry_data):
    print "= %d =" % entry_data.year
    for section in entry_data.sections:
        sys.stderr.write("[ %s ]\n" % section['name'].encode("utf-8"))

        if 'youtube-playlist' not in section:
            if not has_youtube_entries(section):
                continue
            print "Creating playlist"
            section['youtube-playlist'] = create_playlist(
                yt_service, entry_data, section)
            time.sleep(5)
        playlist = get_playlist(yt_service, section)
        modify_youtube_playlist(yt_service, playlist, section)

        section_entries = map(
            str,
            filter(lambda x: x is not None,
                   (entry.get('youtube', None)
                    for entry in section['entries'])))
        section_entries_set = set(section_entries)

        youtube_entries = fetch_youtube_playlist_entries(yt_service, section)

        youtube_entries_set = set([x["snippet"]["resourceId"]["videoId"] for x in youtube_entries])

        missing_playlist_items = section_entries_set - youtube_entries_set

        missing_entries = []

        sorted_entries = sorted(
            section['entries'],
            lambda x, y: cmp(x.get('position', 999), y.get('position', 999)))
        for entry in sorted_entries:
            if str(entry.get('youtube', '')) in missing_playlist_items:
                missing_entries.append(entry)

        for entry in missing_entries:
            youtube_id = entry['youtube']
            asmyoutube.try_operation(
                u"Adding %s (%s)" % (entry['title'], youtube_id),
                lambda: yt_service.playlistItems().insert(
                    part="snippet",
                    body=dict(
                        snippet=dict(
                            playlistId=section["youtube-playlist"],
                            resourceId=dict(
                                kind="youtube#video",
                                videoId=youtube_id)))).execute(),
                sleep=1)


def main(argv=sys.argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile")
    parser.add_argument("--sections", default="")
    asmyoutube.add_auth_args(parser)
    args = parser.parse_args(argv[1:])
    yt_service = asmyoutube.get_authenticated_service(args)

    entry_data = asmmetadata.parse_file(open(args.datafile, "rb"))

    result = os.EX_OK

    try:
        update_youtube_playlists(yt_service, entry_data)
    except KeyboardInterrupt:
        result = os.DATAERR
        print "Interrupted"
    except Exception, e:
        result = os.EX_SOFTWARE
        print "EXCEPTION Unknown exception happened: %s" % e.message

    fp = open(args.datafile, "wb")
    asmmetadata.print_metadata(fp, entry_data)
    return result


if __name__ == "__main__":
    sys.exit(main(sys.argv))
