import argparse
import asmmetadata
import os.path
import sys
import subprocess
import time

parser = argparse.ArgumentParser(description='Upload videos to Youtube.')
parser.add_argument('email')
parser.add_argument('password')
parser.add_argument('files_root', metavar="files-root")
parser.add_argument('--video-postfix', default=".mp4")
parser.add_argument('--dry-run', action="store_true")
commandline_args = parser.parse_args(sys.argv[1:])

email = commandline_args.email
password = commandline_args.password
files_root = commandline_args.files_root
video_postfix = commandline_args.video_postfix

def call_and_capture_output(args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    output, errors = p.communicate()
    outlines = output.strip().split("\n")
    return outlines

sleep_function = time.sleep
if commandline_args.dry_run:
    sleep_function = lambda x : None
    def call_and_capture_output(args):
        return [""]

yearline = sys.stdin.readline().strip()

print yearline

data_type, year = yearline.split(" ", 1)
assert data_type == ":year"

failures = 0

zero_position = 1

for line in sys.stdin:
    sys.stdout.flush()
    # Fast-forward if there are over 2 consecutive failures.
    # Youtube is probably blocking then and we need to wait 10 minutes.
    if failures > 2:
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
            zero_position = 1
            section = value
        continue

    entryinfo = asmmetadata.parse_entry_line(line)
    entryinfo['section'] = {
        'name': section,
        'year': int(year),
        }

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
        position_filename = "9%02d" % zero_position
    else:
        position_filename = "%02d" % position

    source_file_base = asmmetadata.normalize_key(
        "%s-%s-%s-%s-by-%s" % (
            year,
            section,
            position_filename,
            title,
            author)
        )
    source_file = os.path.join(files_root, year, source_file_base + video_postfix)

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

    if os.path.getsize(source_file) > (2**31 - 1):
        print "# XXX not-uploaded over 2GB file!"
        print line.encode('utf-8')
        sys.stderr.write("# XXX not-uploaded over 2GB file!\n")
        sys.stderr.write("%s\n" % youtube_title)
        sys.stderr.write("%s\n" % description)
        sys.stderr.write("%s\n" % category)
        sys.stderr.write("%s\n" % ", ".join(tag_list))
        continue

    tags = ",".join(tag_list)

    upload_trials = 0
    args = ['youtube-upload', '--no-split', '--', email, password, video_file, youtube_title, description, category, tags]
    upload_success = False
    youtube_id = ''
    # 3 trials to upload video with one extra retry chance.
    while upload_success == False and upload_trials < 3:
        if upload_trials == 2:
            sys.stderr.write("YOUTUBE is blocking, sleeping for 10 minutes!\n")
            sys.stderr.write("%s\n" % time.strftime("%H:%M:%S"))
            # Youtube is probably blocking and we need to wait for 10 minutes.
            sleep_function(601)
        upload_trials += 1
        outlines = call_and_capture_output(args)
        if 'youtube.com' in outlines[-1]:
            upload_success = True
            youtube_http_id = outlines[-1]
            youtube_id = "|youtube:" + youtube_http_id.replace("https://www.youtube.com/watch?v=", "")
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
    sys.stderr.write("done\n")
    # 61 seconds delay between sends is OK, 57 is not.
    sleep_function(61)
