import argparse
import asmmetadata
import requests
import sys
import xml.dom.minidom

parser = argparse.ArgumentParser()
parser.add_argument("metadata_file")
parser.add_argument("elaine_vods_url")
parser.add_argument("elaine_pms_vodlist_url")
args = parser.parse_args()

metadata_fp = open(args.metadata_file, "rb")
metadata = asmmetadata.parse_file(metadata_fp)

vodlist_result = requests.get(args.elaine_pms_vodlist_url)
if vodlist_result.status_code != 200:
    sys.stderr.write(
        "Vodlist request to %s failed\n" % args.elaine_pms_vodlist_url)
    sys.exit(1)
vodlist = vodlist_result.text

elaine_pms_map = {}

for line in vodlist.split("\n"):
    elaine_id, pms_id = (line.split(":", 1) + ["", ""])[:2]
    if not pms_id:
        continue
    elaine_pms_map[elaine_id] = pms_id

vod_xml_result = requests.get(args.elaine_vods_url)
if vod_xml_result.status_code != 200:
    sys.stderr.write(
        "Vod request to %s failed\n" % args.elaine_vods_url)
    sys.exit(1)

vod_xml = vod_xml_result.text

elaine_doc = xml.dom.minidom.parseString(vod_xml)

items = elaine_doc.getElementsByTagName("item")


def get_highest_bitrate_media_element(item):
    highest_bitrate = -1
    highest_element = None
    for content in item.getElementsByTagName("media:content"):
        bitrate = int(content.getAttribute("bitrate"))
        if bitrate > highest_bitrate:
            highest_bitrate = bitrate
            highest_element = content
    return highest_element

pms_elaine_files = {}

for item in items:
    guid = item.getElementsByTagName("guid")[0].firstChild.nodeValue
    elaine_id = guid.split("/")[-1]
    if elaine_id not in elaine_pms_map:
        continue
    media_element = get_highest_bitrate_media_element(item)
    media_url = media_element.getAttribute("url")
    filename = media_url.replace("http://media.assembly.org", "")
    pms_id = elaine_pms_map[elaine_id]
    pms_elaine_files[pms_id] = filename


for entry in metadata.entries:
    if not 'pms-id' in entry:
        continue
    pms_id = entry['pms-id']
    if not pms_id in pms_elaine_files:
        continue
    entry['media'] = pms_elaine_files[pms_id]

asmmetadata.print_metadata(sys.stdout, metadata)
