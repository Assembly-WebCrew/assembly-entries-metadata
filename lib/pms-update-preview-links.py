import argparse
import asmmetadata
import compodata

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

metadata_fp = open(args.metadata_file, "rb")
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
        print "FAILED to find corresponding entry for %s" % (str(metadata_entry))
        continue

    preview_link = None
    if 'youtube' in updatable_entry:
        preview_link = u"http://www.youtube.com/watch?v=%s" % updatable_entry['youtube']

    if 'image-file' in updatable_entry:
        key = asmmetadata.get_entry_key(updatable_entry)
        preview_link = u"http://archive.assembly.org/%d/%s/%s" % (
            metadata.year, updatable_entry['section']['key'], key)

    if not preview_link:
        preview_link = ''
        print "NO PREVIEW %s %s" % (pms_entry['id'], pms_entry['title'])

    if pms_entry.get('preview', '') != preview_link:
        compodata.update_entry_preview(
            args.pms_root,
            args.pms_login,
            args.pms_password,
            updatable_entry['pms-id'],
            preview_link)
    else:
        print "Preview link already exists %s" % updatable_entry['pms-id']
