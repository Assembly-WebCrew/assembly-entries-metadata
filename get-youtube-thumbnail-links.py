import asmmetadata
import sys

data = asmmetadata.parse_file(sys.stdin)

for entries in data.entries.values():
    for entry in entries:
        if 'youtube' not in entry:
            continue
        youtube_id = entry['youtube']
        # Make sure that there are no http://youtube.com/ style IDs.
        assert "/" not in youtube_id
        print "http://i.ytimg.com/vi/%s/0.jpg" % youtube_id
