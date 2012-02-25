import asmmetadata
import gdata.youtube
import gdata.youtube.service
import optparse
import sys
import time
import urllib

YOUTUBE_MAX_TITLE_LENGTH = 100

parser = optparse.OptionParser()

(options, args) = parser.parse_args()
if len(args) != 5:
    parser.error("Usage: datafile developer-key youtube-username email password")

datafile, youtube_developer_key, youtube_username, email, password = sys.argv[1:]

def get_ordinal_suffix(number):
    suffixes = {1: 'st',
               2: 'nd',
               3: 'rd'}
    suffix = suffixes.get(number % 10, 'th')
    if number in [11, 12, 13]:
        suffix = 'th'
    return suffix

def get_youtube_info_data(entry):
    title = entry['title']
    author = entry['author']
    section_name = entry['section']['name']
    if "AssemblyTV" in section_name or "Seminars" in section_name or "Winter" in section_name:
        name = title
    else:
        name = "%s by %s" % (title, author)

    position = entry.get('position', 0)

    description = u""
    if 'warning' in entry:
        description += u"%s\n\n" % entry['warning']

    position_str = None

    if position != 0:
        position_str = str(position) + get_ordinal_suffix(position) + " place"

    party_name = asmmetadata.get_party_name(
        entry['section']['year'], entry['section']['name'])

    display_author = None
    if not "AssemblyTV" in section_name and not "Winter" in section_name:
        display_author = author
        if not "Seminars" in section_name:
            description += "%s competition entry, " % party_name
            if entry['section'].get('ongoing', False) is False:
                if position_str is not None:
                    description += u"%s" % position_str
                else:
                    description += u"not qualified to be shown on the big screen"
                description += u".\n\n"
        else:
            description += u"%s seminar presentation.\n\n" % party_name
    elif "AssemblyTV" in section_name:
        description += u"%s AssemblyTV program.\n\n" % party_name

    if 'description' in entry:
        description += u"%s\n\n" % entry['description']

    if 'platform' in entry:
        description += u"Platform: %s\n" % entry['platform']

    if 'techniques' in entry:
        description += u"Notes: %s\n" % entry['techniques']

    description += u"Title: %s\n" % title
    if display_author is not None:
        description += u"Author: %s\n" % display_author

    description += "\n"

    if 'download' in entry:
        download = entry['download']
        download_type = "Download original:"
        if "game" in section_name.lower():
            download_type = "Download playable game:"
        description += "%s: %s" % (download_type, download)

    if 'sceneorg' in entry:
        sceneorg = entry['sceneorg']
        download_type = "original"
        if "game" in section_name.lower():
            download_type = "playable game"
        if "," in sceneorg:
            parts = sceneorg.split(",")
            i = 1
            for part in parts:
                description += "Download %s part %d/%d: http://www.scene.org/file.php?file=%s\n" % (
                    download_type, i, len(parts), urllib.quote_plus(part))
                i += 1
        else:
            description += "Download %s: http://www.scene.org/file.php?file=%s\n" % (
                download_type, urllib.quote_plus(part))

    if 'sceneorgvideo' in entry:
        sceneorgvideo = entry['sceneorgvideo']
        description += "Download high quality video: http://www.scene.org/file.php?file=%s\n" % urllib.quote_plus(sceneorgvideo)
    elif 'media' in entry:
        mediavideo = entry['media']
        description += "Download high quality video: http://media.assembly.org%s\n" % mediavideo

    tags = set(asmmetadata.get_party_tags(
            entry['section']['year'], entry['section']['name']))

    if 'tags' in entry:
        tags.update(entry['tags'].split(" "))

    if "AssemblyTV" in entry['section']['name'] or "Winter" in entry['section']['name']:
        tags.add("AssemblyTV")

    description_non_unicode = description.encode("utf-8")

    return {
        'title': name[:YOUTUBE_MAX_TITLE_LENGTH].encode("utf-8"),
        'description': description_non_unicode,
        'tags': list(tags),
        }

def try_youtube_operation(label, function, retries=3, sleep=5):
    success = False
    retry_count = 0
    while not success and retry_count < retries:
        retry_count += 1
        print "Try %d: %s" % (retry_count, label)
        result = function()
        time.sleep(sleep)
        if result is not None:
            success = True
            break
    if success:
        return result
    print "Failed: %s. Sleeping for 600 seconds." % label
    time.sleep(600)
    return None

def update_youtube_info(yt_service, username, entry_data):
    for entry in entry_data.entries:
        if not 'youtube' in entry:
            continue
        update_youtube_info_entry(yt_service, username, entry)

def update_youtube_info_entry(yt_service, username, entry):
    youtube_info = get_youtube_info_data(entry)

    uri = 'https://gdata.youtube.com/feeds/api/users/%s/uploads/%s' % (username, entry['youtube'])

    youtube_entry = try_youtube_operation(
        "get info for %s" % youtube_info['title'],
        lambda: yt_service.GetYouTubeVideoEntry(uri=uri))
    if youtube_entry is None:
        return

    update_entry = False
    if youtube_entry.media.title.text != youtube_info['title']:
        update_entry = True
        youtube_entry.media.title.text = youtube_info['title']
    if youtube_entry.media.description.text != youtube_info['description'].strip():
        update_entry = True
        youtube_entry.media.description.text = youtube_info['description'].strip()
    existing_tags = sorted([tag.strip().lower() for tag in youtube_entry.media.keywords.text.split(",")])
    if existing_tags != sorted([tag.strip().lower() for tag in youtube_info['tags']]):
        update_entry = True
        youtube_entry.media.keywords.text = ", ".join(youtube_info['tags'])

    if update_entry:
        try_youtube_operation(
            "update %s" % youtube_info['title'],
            lambda: yt_service.UpdateVideoEntry(youtube_entry))

yt_service = gdata.youtube.service.YouTubeService()

# Note: SSL is not available at this time for uploads.
yt_service.ssl = True
#yt_service.debug = True

yt_service.developer_key = youtube_developer_key
yt_service.client_id = 'ASM-playlist-updater'
yt_service.email = email
yt_service.password = password
yt_service.source = 'ASM-playlist-updater'
yt_service.ProgrammaticLogin()

entry_data = asmmetadata.parse_file(open(datafile, "rb"))

try:
    update_youtube_info(yt_service, youtube_username, entry_data)
except KeyboardInterrupt, e:
    print "Interrupted"
