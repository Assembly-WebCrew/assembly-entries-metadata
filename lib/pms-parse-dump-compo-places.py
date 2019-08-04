#!/usr/bin/env python3

import argparse
import sys
import xml.dom.minidom

parser = argparse.ArgumentParser()
parser.add_argument("datafile")
parser.add_argument("pms_datafile")
args = parser.parse_args()

pms_dom = xml.dom.minidom.parse(open(args.pms_datafile, "r"))

iddata = {}

compos = pms_dom.getElementsByTagName("compo")

for compo in compos:
    if compo.getAttribute("resultspublic") != "True":
        continue
    entries = compo.getElementsByTagName("entry")
    for entry in entries:
        entry_id = entry.getAttribute("id")
        entry_position_str = entry.getAttribute("place") or '0'
        techniques = entry.getAttribute("techniques")
        if len(techniques) == 0:
            techniques = None
        platform = entry.getAttribute("platform")
        if len(platform) == 0:
            platform = None
        entry_position = int(entry_position_str) or None
        iddata[entry_id] = (entry_position, techniques, platform)

import asmmetadata

parsed = asmmetadata.parse_file(open(args.datafile))

for entry in parsed.entries:
    if 'pms-id' not in entry:
        continue
    _, _, pms_id = entry['pms-id'].split("/")
    if pms_id not in iddata:
        # This probably means that results of a category are not public.
        continue
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
