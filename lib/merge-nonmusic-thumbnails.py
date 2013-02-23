import asmmetadata
import optparse
import os
import os.path
import sys

parser = optparse.OptionParser()

(options, args) = parser.parse_args()
if len(args) != 2:
    parser.error("Usage: program fileroot merge_limit")
fileroot = args[0]
merge_limit = int(args[1])

entry_data = asmmetadata.parse_file(sys.stdin)

def create_merged_image(fileroot, start, entries):
    outfile_base = asmmetadata.create_merged_image_base(start, entries)
    out_filename_png = os.path.join(fileroot, "thumbnails/small/%s.png" % outfile_base)
    out_filename_jpeg = os.path.join(fileroot, "thumbnails/small/%s.jpeg" % outfile_base)
    thumbnail_paths = []
    for entry in entries:
        thumbnail_base = asmmetadata.select_thumbnail_base(entry)
        thumbnail_paths.append(os.path.join(fileroot, thumbnail_base + '.png'))
    print 'mkdir -p "%s"' % os.path.join(fileroot, "thumbnails/merged/")
    print 'convert "%s" +append "%s"' % ('" "'.join(thumbnail_paths), out_filename_png)
    print 'convert "%s" +append "%s"' % ('" "'.join(thumbnail_paths), out_filename_jpeg)
    print 'optipng -o7 "%s"' % out_filename_png
    print 'jpegoptim --strip-all "%s"' % out_filename_jpeg

# def create_merged_entry_groups(entries

for section in entry_data.sections:
    if 'music' in section['name'].lower():
        continue
    merge_entries = []
    start = 1
    for entry in asmmetadata.sort_entries(section['entries']):
        if len(merge_entries) == merge_limit:
            create_merged_image(fileroot, start, merge_entries)
            start += len(merge_entries)
            item_count = 0
            merge_entries = []
        thumbnail = asmmetadata.select_thumbnail_base(entry)
        if thumbnail is not None:
            merge_entries.append(entry)
    if len(merge_entries) > 0:
        create_merged_image(fileroot, start, merge_entries)
