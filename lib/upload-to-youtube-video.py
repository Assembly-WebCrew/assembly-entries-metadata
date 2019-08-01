#!/usr/bin/env python
import argparse
import asmmetadata
import asmyoutube
import os.path
import re
import sys
import subprocess
import time

ABORT_FAILURES = 2
UPLOAD_TRIALS = 3
# 10 minutes is the definite minimum sleeping time in Youtube for retries.
YOUTUBE_MINIMUM_SLEEP_TIME = 601


def call_and_capture_output_real(args):
    sys.stderr.write("%s\n" % args)
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = p.communicate()
    outlines = output.strip().split("\n")
    outlines.extend(errors.strip().split("\n"))
    return outlines


def call_and_capture_output_fake(args):
    return ["http://www.youtube.com/watch?v=asdf"]


class State:
    def __init__(self, files_root, media_vod_directory):
        self.files_root = files_root
        self.media_vod_directory = media_vod_directory
        self.failures = 0
        self.zero_position = 1


def handle_entry(
        call_and_capture_output,
        sleep_function,
        privacy,
        state,
        entry):
    if "youtube" in entry:
        return
    # Fast-forward if there are many consecutive failures.
    # Youtube is probably blocking then and we need to wait 10 minutes.
    if state.failures > ABORT_FAILURES:
        raise RuntimeError(
            "Failures %d exceeded abort failures %d!",
            state.failures, ABORT_FAILURES)

    source_file = "oaisdfjtTODOD"
    # source_file_base = asmmetadata.normalize_key(
    #     "%s-%s%s-%s-by-%s" % (
    #         year,
    #         section,
    #         position_filename,
    #         title,
    #         author)
    #     )
    # source_file = os.path.join(
    #     files_root, year, source_file_base + video_postfix)

    if not os.path.exists(source_file) and 'video-file' in entry:
        source_file = os.path.join(state.files_root, entry['video-file'])

    if not os.path.exists(source_file):
        return

    video_file = source_file

    youtube_data = asmmetadata.get_youtube_info_data(entry)
    youtube_title = youtube_data['title']
    description = youtube_data['description']
    category = youtube_data['category']
    tag_list = youtube_data['tags']

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
        #sys.stderr.write("%s\n" % outlines)
        youtube_id = asmyoutube.get_video_id_try_url(outlines[0])
        if youtube_id:
            upload_success = True
            state.failures = 0
        else:
            sys.stderr.write("UPLOAD failed %s\n" % youtube_title)
            sys.stderr.write("\n".join(outlines))
            sys.stderr.write(youtube_title)
            sys.stderr.write("\n")
            sys.stderr.write(description)
            sys.stderr.write("\n")
            sys.stderr.write(tags)
            sys.stderr.write("\n")

    if upload_success:
        state.failures = 0
    else:
        state.failures += 1

    if youtube_id is not None:
        entry["youtube"] = youtube_id
    # 61 seconds delay between sends is OK, 57 is not.
    sleep_function(61)


def main(argv):
    parser = argparse.ArgumentParser(description='Upload videos to Youtube.')
    parser.add_argument('metadata_file', metavar="metadata-file")
    parser.add_argument('files_root', metavar="files-root")
    parser.add_argument('--video-postfix', default=".mp4")
    parser.add_argument('--dry-run', action="store_true")
    parser.add_argument('--media-vod-directory')
    parser.add_argument(
        '--privacy', default="public", choices=["public", "unlisted", "private"])
    args = parser.parse_args(argv[1:])

    files_root = args.files_root
    video_postfix = args.video_postfix
    media_vod_directory = args.media_vod_directory
    privacy = args.privacy

    sleep_function = time.sleep
    if args.dry_run:
        sleep_function = lambda x : None
        call_and_capture_output = call_and_capture_output_fake
    else:
        call_and_capture_output = call_and_capture_output_real

    metadata = asmmetadata.parse_file(open(args.metadata_file, "r"))

    state = State(
        files_root=files_root,
        media_vod_directory=media_vod_directory)

    try:
        for entry in metadata.entries:
            handle_entry(
                call_and_capture_output, sleep_function, privacy, state, entry)
    except:
        asmmetadata.print_metadata(
            open(args.metadata_file, "w"), metadata)
        raise
    asmmetadata.print_metadata(
        open(args.metadata_file, "w"), metadata)
    if args.dry_run:
        return 1
    return os.EX_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
