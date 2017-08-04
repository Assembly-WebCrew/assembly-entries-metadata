#!/usr/bin/env python
import argparse
import asmmetadata
import os.path
import re
import sys
import subprocess
import time

ABORT_FAILURES = 2
UPLOAD_TRIALS = 3
# 10 minutes is the definite minimum sleeping time in Youtube for retries.
YOUTUBE_MINIMUM_SLEEP_TIME = 601

parser = argparse.ArgumentParser(description='Upload videos to Youtube.')
parser.add_argument('files_root', metavar="files-root")
parser.add_argument('--video-postfix', default=".mp4")
parser.add_argument('--dry-run', action="store_true")
parser.add_argument('--media-vod-directory')
parser.add_argument(
    '--privacy', default="public", choices=["public", "unlisted", "private"])
commandline_args = parser.parse_args(sys.argv[1:])

files_root = commandline_args.files_root
video_postfix = commandline_args.video_postfix
media_vod_directory = commandline_args.media_vod_directory
privacy = commandline_args.privacy


def call_and_capture_output_real(args):
    sys.stderr.write("%s\n" % args)
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = p.communicate()
    outlines = output.strip().split("\n")
    outlines.extend(errors.strip().split("\n"))
    return outlines


def call_and_capture_output_fake(args):
    return ["http://www.youtube.com/watch?v=asdf"]

sleep_function = time.sleep
if commandline_args.dry_run:
    sleep_function = lambda x : None
    call_and_capture_output = call_and_capture_output_fake
else:
    call_and_capture_output = call_and_capture_output_real

yearline = sys.stdin.readline().strip()

print yearline

data_type, year = yearline.split(" ", 1)
assert data_type == ":year"

failures = 0

zero_position = 1

section_data = {}

for line in sys.stdin:
    sys.stdout.flush()
    # Fast-forward if there are many consecutive failures.
    # Youtube is probably blocking then and we need to wait 10 minutes.
    if failures > ABORT_FAILURES:
        sys.stdout.write(line)
        continue

    try:
        line = unicode(line.strip(), "utf-8")
    except ValueError, e:
        # Why is this happening?
        sys.stdout.write(line)
        continue

    if line == "":
        print
        continue

    if line[0] == "#":
        print line.encode("utf-8")
        continue

    if line[0] == ":":
        print line.encode('utf-8')
        data_type, value = line.split(" ", 1)
        if data_type == ":section":
            section_data = {
                'name': value,
                'year': int(year)
                }
            zero_position = 1
            section = section_data['name']
        else:
            section_data[str(data_type.lstrip(":"))] = value
        continue

    entryinfo = asmmetadata.parse_entry_line(line)
    entryinfo['section'] = section_data

    author = entryinfo.get("author", None)
    title = entryinfo.get("title", None)
    if title is None or author is None:
        sys.stderr.write(("FAILED to get author or title %s\n" % line).encode('utf-8'))
        print line.encode('utf-8')
        continue

    title = title.replace("<", "-").replace(">", "-")
    author = author.replace("<", "-").replace(">", "-")

    position = entryinfo.get('position', None)
    if position is None:
        #position_filename = "9%02d" % zero_position
        position_filename = "-99"
    else:
        position_filename = "-%02d" % position

    if section.lower() in ["misc", "assemblytv", "winter", "seminars"]:
        position_filename = ""

    source_file_base = asmmetadata.normalize_key(
        "%s-%s%s-%s-by-%s" % (
            year,
            section,
            position_filename,
            title,
            author)
        )
    source_file = os.path.join(
        files_root, year, source_file_base + video_postfix)

    if not os.path.exists(source_file) and 'video-file' in entryinfo:
        source_file = os.path.join(files_root, entryinfo['video-file'])

    if not os.path.exists(source_file) and 'media' in entryinfo and not media_vod_directory is None:
        source_file = os.path.join(media_vod_directory, entryinfo['media'].lstrip("/"))

    if not os.path.exists(source_file):
        print line.encode('utf-8')
        continue

    if position is None:
        zero_position += 1

    video_file = source_file

    youtube_data = asmmetadata.get_youtube_info_data(entryinfo)
    youtube_title = youtube_data['title']
    description = youtube_data['description']
    category = youtube_data['category']
    tag_list = youtube_data['tags']

    if 'youtube' in entryinfo:
        print line.encode('utf-8')
        continue

    tags = ",".join(tag_list)

    args = [
        '/home/jussi/.local/bin/youtube-upload',
        '--category', category,
        '--tags', tags,
        '--title', youtube_title,
        '--description', description,
#        '--credentials-file', 'client_secrets.json',
        video_file]
    args.append("--privacy=%s" % privacy)
    upload_success = False
    youtube_id = ''
    upload_trials = 1
    # 3 trials to upload video with one extra retry chance.
    while not upload_success and upload_trials < UPLOAD_TRIALS:
        if upload_trials == UPLOAD_TRIALS:
            sys.stderr.write("YOUTUBE is blocking, sleeping for 10 minutes!\n")
            sys.stderr.write("%s\n" % time.strftime("%H:%M:%S"))
            sleep_function(YOUTUBE_MINIMUM_SLEEP_TIME)
        upload_trials += 1
        outlines = call_and_capture_output(args)
        if 'youtube.com' in outlines[-1]:
            upload_success = True
            youtube_http_id = outlines[-1]
            youtube_http_id = re.sub(
                r"^(.+?)https?://www\.youtube\.com/watch\?v=", "", youtube_http_id)
            youtube_id = "|youtube:" + youtube_http_id
            failures = 0
        else:
            sys.stderr.write(("UPLOAD failed %s\n" % line).encode('utf-8'))
            sys.stderr.write("\n".join(outlines))
            sys.stderr.write(youtube_title.encode('utf-8'))
            sys.stderr.write("\n")
            sys.stderr.write(description.encode('utf-8'))
            sys.stderr.write("\n")
            sys.stderr.write(tags)
            sys.stderr.write("\n")

    if upload_success:
        failures = 0
    else:
        failures += 1
    print (line + youtube_id).encode('utf-8')
    sys.stdout.flush()
    sys.stderr.write("%s - %s done\n" % (youtube_title, youtube_id))
    # 61 seconds delay between sends is OK, 57 is not.
    sleep_function(61)
