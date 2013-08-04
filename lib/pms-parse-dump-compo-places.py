import argparse
import sys
import xml.dom.minidom

parser = argparse.ArgumentParser()
parser.add_argument("datafile")
parser.add_argument("pms_datafile")
args = parser.parse_args()

pms_dom = xml.dom.minidom.parse(open(args.pms_datafile, "rb"))

entries = pms_dom.getElementsByTagName("entry")

iddata = {}

for entry in entries:
    entry_id = entry.getAttribute("id")
    entry_position = entry.getAttribute("place")
    techniques = entry.getAttribute("techniques")
    if len(techniques) == 0:
        techniques = None
    platform = entry.getAttribute("platform")
    if len(platform) == 0:
        platform = None
    iddata[entry_id] = (int(entry_position), techniques, platform)

import asmmetadata

parsed = asmmetadata.parse_file(open(args.datafile))

for entry in parsed.entries:
    if 'pms-id' not in entry:
        continue
    _, _, pms_id = entry['pms-id'].split("/")
    place, techniques, platform = iddata[pms_id]
    entry['position'] = place
    if techniques is not None:
        # techniques = techniques.replace("\\", "\\\\")
        # techniques = techniques.replace("\n", "\\n")
        entry['techniques'] = techniques
    if platform is not None:
        entry['platform'] = platform

for section in parsed.sections:
    asmmetadata.reorder_positioned_section_entries(section['entries'])

asmmetadata.print_metadata(sys.stdout, parsed)
