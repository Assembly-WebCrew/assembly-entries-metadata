import asmmetadata
import gdata.youtube
import gdata.youtube.service
import re
import sys
import time
import urlparse

datafile, youtube_developer_key, youtube_user, email, password = sys.argv[1:]

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
    for section in entry_data.sections:
        sys.stderr.write("[%s]\n" % section['name'].encode("utf-8"))
        if 'youtube-playlist' not in section:
            if not has_youtube_entries(section):
                continue
            print "Creating playlist"
            section['youtube-playlist'] = create_playlist(entry_data, section)
            time.sleep(10)

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
            time.sleep(5)
        time.sleep(10)

yt_service = gdata.youtube.service.YouTubeService()

# The YouTube API does not currently support HTTPS/SSL access.
yt_service.ssl = False

yt_service.developer_key = youtube_developer_key
yt_service.client_id = 'ASM-playlist-updater'
yt_service.email = email
yt_service.password = password
yt_service.source = 'ASM-playlist-updater'
yt_service.ProgrammaticLogin()

entry_data = asmmetadata.parse_file(open(datafile, "rb"))

try:
    update_youtube_playlists(yt_service, entry_data)
except KeyboardInterrupt, e:
    print "Interrupted"
except:
    print "Unknown exception happened"

fp = open(datafile, "wb")
asmmetadata.print_metadata(fp, entry_data)
