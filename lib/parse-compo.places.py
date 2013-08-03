import sys
import xml.dom.minidom

dom = xml.dom.minidom.parse(open(sys.argv[1], "rb"))

entries = dom.getElementsByTagName("entry")

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

parsed = asmmetadata.parse_file(sys.stdin)

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

asmmetadata.print_metadata(sys.stdout, parsed)
