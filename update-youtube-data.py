import asmmetadata
import gdata.youtube
import gdata.youtube.service
import optparse
import sys
import time

parser = optparse.OptionParser()

(options, args) = parser.parse_args()
if len(args) != 5:
    parser.error(
        "Usage: datafile developer-key youtube-username email password")

(datafile,
 youtube_developer_key,
 youtube_username,
 email,
 password) = sys.argv[1:]


def try_youtube_operation(label, function, retries=3, sleep=4):
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
    youtube_info = asmmetadata.get_youtube_info_data(entry)

    uri = 'https://gdata.youtube.com/feeds/api/users/%s/uploads/%s' \
        % (username, entry['youtube'])

    youtube_entry = try_youtube_operation(
        "get info for %s" % youtube_info['title'],
        lambda: yt_service.GetYouTubeVideoEntry(uri=uri),
        sleep=1)
    if youtube_entry is None:
        return

    update_entry = False
    if youtube_entry.media.title.text != youtube_info['title']:
        update_entry = True
        youtube_entry.media.title.text = youtube_info['title']
    if youtube_entry.media.description.text != youtube_info['description'].strip():
        update_entry = True
        youtube_entry.media.description.text = youtube_info['description'].strip()
    existing_tags = []
    if youtube_entry.media.keywords.text is not None:
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
