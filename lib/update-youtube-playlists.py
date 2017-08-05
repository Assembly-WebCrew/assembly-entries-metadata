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


def create_playlist(yt_service, entry_data, section, privacy):
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
                privacyStatus=privacy
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


def playlist_modify_info(yt_service, playlist, section):
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


def get_section_youtube_ids(section):
    return map(
        str,
        filter(lambda x: x is not None,
               (entry.get('youtube', None)
                for entry in section['entries'])))


def playlist_add_new_items(yt_service, youtube_entries, section):
    section_entries_set = set(get_section_youtube_ids(section))

    youtube_entries_set = set(
        [x["snippet"]["resourceId"]["videoId"] for x in youtube_entries])

    missing_playlist_items = section_entries_set - youtube_entries_set

    sorted_entries = sorted(
        section['entries'],
        lambda x, y: cmp(x.get('position', 999), y.get('position', 999)))
    missing_entries = []
    for entry in sorted_entries:
        if str(entry.get('youtube', '')) in missing_playlist_items:
            missing_entries.append(entry)

    if len(missing_entries) == 0:
        return youtube_entries

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
    return fetch_youtube_playlist_entries(yt_service, section)


def playlist_remove_extra(yt_service, youtube_entries, section):
    section_ids_set = set(get_section_youtube_ids(section))
    known_ids = set()
    modified = False
    for youtube_entry in youtube_entries:
        video_id = youtube_entry["snippet"]["resourceId"]["videoId"]
        video_title = youtube_entry["snippet"]["title"]
        if video_id in known_ids:
            modified = True
            asmyoutube.try_operation(
                u"Removing duplicate entry %s: %s" % (video_id, video_title),
                lambda: yt_service.playlistItems().delete(
                    id=youtube_entry["id"]).execute())
        known_ids.add(video_id)

        if video_id not in section_ids_set:
            modified = True
            asmyoutube.try_operation(
                u"Removing unknown entry %s: %s" % (video_id, video_title),
                lambda: yt_service.playlistItems().delete(
                    id=youtube_entry["id"]).execute())

    if not modified:
        return youtube_entries

    return fetch_youtube_playlist_entries(yt_service, section)


def playlist_reorder_entries(yt_service, youtube_entries, section):
    """Reorders youtube playlist entries into a correct order

    Reordering is done by using a heuristic where the item that needs to
    be moved the most is always moved to the correct position each
    iteration.
    """

    positions = {}
    for position, video_id in enumerate(get_section_youtube_ids(section)):
        positions[video_id] = position

    entries_video_id = {}
    for youtube_entry in youtube_entries:
        video_id = youtube_entry["snippet"]["resourceId"]["videoId"]
        entries_video_id[video_id] = youtube_entry

    modified = False
    # We shouldn't exceed the amount of entries when doing playlist
    # reorderings:
    for _ in xrange(len(positions)):
        position_changes = {}
        for youtube_entry in youtube_entries:
            video_id = youtube_entry["snippet"]["resourceId"]["videoId"]
            position = youtube_entry["snippet"]["position"]
            position_changes[video_id] = positions[video_id] - position

        max_change_abs = 0
        max_change_id = None
        max_change_position = -1

        # Find max position change:
        for video_id, position_change in position_changes.items():
            # First condition finds the one that we move the most.
            # Second condition optimizes the movements when we move multiple
            # playlist items.
            if (abs(position_change) > max_change_abs or
                (abs(position_change) == max_change_abs and
                    positions[video_id] < max_change_position)):
                max_change_abs = abs(position_change)
                max_change_id = video_id
                max_change_position = positions[video_id]
        if max_change_abs == 0:
            break

        max_change_amount = position_changes[max_change_id]
        max_change_entry = entries_video_id[max_change_id]
        old_position = max_change_entry["snippet"]["position"]
        new_position = old_position + max_change_amount

        if max_change_amount < 0:
            for youtube_entry in youtube_entries:
                if youtube_entry["snippet"]["position"] > old_position:
                    continue
                if youtube_entry["snippet"]["position"] < new_position:
                    continue
                youtube_entry["snippet"]["position"] += 1
        else:
            for youtube_entry in youtube_entries:
                if youtube_entry["snippet"]["position"] < old_position:
                    continue
                if youtube_entry["snippet"]["position"] > new_position:
                    continue
                youtube_entry["snippet"]["position"] -= 1

        max_change_entry["snippet"]["position"] = new_position
        asmyoutube.try_operation(
            u"Updating position %d->%d: %s" % (
                old_position,
                new_position,
                max_change_entry["snippet"]["title"]),
            lambda: yt_service.playlistItems().update(
                part="snippet",
                body=dict(
                    playlistId=section["youtube-playlist"],
                    id=max_change_entry["id"],
                    snippet=max_change_entry["snippet"])
            ).execute()
        )

    if not modified:
        return youtube_entries

    return fetch_youtube_playlist_entries(yt_service, section)


def update_youtube_playlists(yt_service, entry_data, sections, privacy):
    print "= %d =" % entry_data.year
    for section in entry_data.sections:
        if sections and section["key"] not in sections:
            continue
        sys.stderr.write("[ %s ]\n" % section['name'].encode("utf-8"))

        if 'youtube-playlist' not in section:
            if not has_youtube_entries(section):
                continue
            print "Creating playlist"
            section['youtube-playlist'] = create_playlist(
                yt_service, entry_data, section, privacy)
            time.sleep(5)
        playlist = get_playlist(yt_service, section)
        playlist_modify_info(yt_service, playlist, section)
        youtube_entries = fetch_youtube_playlist_entries(yt_service, section)
        youtube_entries = playlist_add_new_items(
            yt_service, youtube_entries, section)
        youtube_entries = playlist_remove_extra(
            yt_service, youtube_entries, section)
        youtube_entries = playlist_reorder_entries(
            yt_service, youtube_entries, section)


def main(argv=sys.argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile")
    parser.add_argument(
        "--privacy", default="public",
        choices=["public", "private", "unlisted"])
    parser.add_argument("--section", default="")
    asmyoutube.add_auth_args(parser)
    args = parser.parse_args(argv[1:])
    yt_service = asmyoutube.get_authenticated_service(args)

    entry_data = asmmetadata.parse_file(open(args.datafile, "rb"))

    result = os.EX_OK

    sections = []
    if args.section:
        sections = [x.strip() for x in args.section.split(",")]

    try:
        update_youtube_playlists(
            yt_service, entry_data, sections, args.privacy)
    except KeyboardInterrupt:
        result = os.DATAERR
        print "Interrupted"
    except Exception, e:
        result = os.EX_SOFTWARE
        print "EXCEPTION Unknown exception happened: %s" % e

    fp = open(args.datafile, "wb")
    asmmetadata.print_metadata(fp, entry_data)
    return result


if __name__ == "__main__":
    sys.exit(main(sys.argv))
