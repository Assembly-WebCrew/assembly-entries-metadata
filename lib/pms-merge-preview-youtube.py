import argparse
import asmmetadata
import compodata
import re

parser = argparse.ArgumentParser()
parser.add_argument("metadata_file")
parser.add_argument("pms_root")
parser.add_argument("pms_party")
parser.add_argument("pms_login")
parser.add_argument("pms_password")
parser.add_argument("pms_compo")
args = parser.parse_args()

pms_url = compodata.pms_path_generator(args.pms_root, args.pms_party)

pms_data = compodata.download_compo_data(
    pms_url, args.pms_login, args.pms_password, args.pms_party, args.pms_compo)
pms_entries_data = compodata.parse_compo_entries(pms_data)

metadata_fp = open(args.metadata_file, "r")
metadata = asmmetadata.parse_file(metadata_fp)

for pms_entry in pms_entries_data:
    full_pms_id = pms_entry['id']

    updatable_entry = None

    for metadata_entry in metadata.entries:
        metadata_pms_id = str(metadata_entry.get('pms-id', ''))
        pms_pms_id = str(full_pms_id)
        if metadata_pms_id == pms_pms_id:
            updatable_entry = metadata_entry
            break

    if updatable_entry is None:
        print("FAILED to find corresponding entry for %s" % (str(metadata_entry)))
        continue

    if not pms_entry.get('preview'):
        print("No preview link for %s" % (str(metadata_entry)))
        continue

    preview_link = pms_entry.get('preview')
    youtube_regex = re.compile("https://www.youtube.com/watch\?v=([^&]+)")
    youtube_match = youtube_regex.match(preview_link)
    if not youtube_match:
        print("Not a Youtube preview for %s" % (str(metadata_entry)))
        continue

    youtube_id = youtube_match.group(1)
    updatable_entry["youtube"] = youtube_id

asmmetadata.print_metadata(open(args.metadata_file, "w"), metadata)
