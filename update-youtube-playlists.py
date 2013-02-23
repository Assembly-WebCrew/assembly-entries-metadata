import argparse
import asmmetadata
import gdata.youtube
import gdata.youtube.service
import re
import sys
import time
import urlparse

def has_youtube_entries(section):
    for entry in section['entries']:
        if 'youtube' in entry:
            return True
    return False

def create_playlist(entry_data, section):
    playlist_title = "%s %s" % (
        asmmetadata.get_party_name(entry_data.year, section['name']),
        asmmetadata.get_long_section_name(section['name'])
        )
    playlist_description = section.get('description', u'')
    playlist_description = re.sub("</p><p>", "\n\n", playlist_description)
    playlist_description = re.sub("<[^>]+>", "", playlist_description)

    new_playlist = yt_service.AddPlaylist(playlist_title, playlist_description)
    if isinstance(new_playlist, gdata.youtube.YouTubePlaylistEntry):
        playlist_url = new_playlist.id.text
        playlist_id = playlist_url.split("/")[-1]
        return playlist_id
    return None

def update_youtube_playlists(yt_service, entry_data):
    print "= %d =" % entry_data.year
    for section in entry_data.sections:
        sys.stderr.write("[ %s ]\n" % section['name'].encode("utf-8"))

        if 'youtube-playlist' not in section:
            if not has_youtube_entries(section):
                continue
            print "Creating playlist"
            section['youtube-playlist'] = create_playlist(entry_data, section)
            time.sleep(5)

        playlist_video_feed = yt_service.GetYouTubePlaylistVideoFeed(
            playlist_id=section['youtube-playlist'])

        section_entries = map(
            str,
            filter(lambda x : x is not None,
                   (entry.get('youtube', None) for entry in section['entries'])))

        youtube_entries = []
        for playlist_video_entry in playlist_video_feed.entry:
            player_url = playlist_video_entry.media.player.url
            query = urlparse.urlparse(player_url).query
            query_params = urlparse.parse_qs(query)
            video_id, = query_params['v']
            youtube_entries.append(video_id)

        if len(youtube_entries) >= 25:
            print "MAX gdata API default entries (25) exceeded on playlist!"
            continue

        section_entries_set = set(section_entries)
        youtube_entries_set = set(youtube_entries)

        missing_playlist_items = section_entries_set - youtube_entries_set

        missing_entries = []

        sorted_entries = sorted(section['entries'], lambda x, y: cmp(x.get('position', 999), y.get('position', 999)))
        for entry in sorted_entries:
            if str(entry.get('youtube', '')) in missing_playlist_items:
                missing_entries.append(entry)

        playlist_uri = playlist_video_feed.id.text
        for entry in missing_entries:
            youtube_id = entry['youtube']
            print u"Adding %s (%s)" % (entry['title'], youtube_id)
            playlist_video_entry = yt_service.AddPlaylistVideoEntryToPlaylist(
                playlist_uri, video_id=youtube_id
                )
            if not isinstance(playlist_video_entry, gdata.youtube.YouTubePlaylistVideoEntry):
                print "Failed to add."
            time.sleep(1)
        time.sleep(2)


def main(args=sys.argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile")
    parser.add_argument("youtube_developer_key")
    parser.add_argument("youtube_user")
    parser.add_argument("email")
    parser.add_argument("password")
    args = parser.parse_args()

    yt_service = gdata.youtube.service.YouTubeService()

    # The YouTube API does not currently support HTTPS/SSL access.
    yt_service.ssl = False

    yt_service.developer_key = args.youtube_developer_key
    yt_service.client_id = 'ASM-playlist-updater'
    yt_service.email = args.email
    yt_service.password = args.password
    yt_service.source = 'ASM-playlist-updater'
    yt_service.ProgrammaticLogin()

    entry_data = asmmetadata.parse_file(open(args.datafile, "rb"))

    try:
        update_youtube_playlists(yt_service, entry_data)
    except KeyboardInterrupt:
        print "Interrupted"
    except:
        print "EXCEPTION Unknown exception happened"

    fp = open(args.datafile, "wb")
    asmmetadata.print_metadata(fp, entry_data)


if __name__ == "__main__":
    main()
