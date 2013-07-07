from __future__ import print_function
import argparse
import asmmetadata
import json
import os.path
import urllib
import urllib2
import urlparse

opener = urllib2.build_opener(
        urllib2.HTTPCookieProcessor(),
        urllib2.HTTPRedirectHandler(),
        )

parser = argparse.ArgumentParser()
parser.add_argument("photos_root")
parser.add_argument("base_url")
parser.add_argument("--download", default=False, action="store_true")
args = parser.parse_args()

no_print = lambda *x: None

print_metadata = print
print_shell = no_print
if args.download:
    print_metadata = no_print
    print_shell = print

base_url = args.base_url
opened = opener.open("http://assembly.galleria.fi/?type=getFolderTree")
data = opened.read()

parsed_url = urlparse.urlparse(base_url)
wanted_path = urllib.unquote_plus(parsed_url.path)

photo_category = os.path.basename(args.photos_root)
event_category = photo_category.replace("photo-", "")
print_metadata(":section Photos %s" % event_category)

paths = json.loads(data)
photographer_paths = dict([
        (path, data) for path, data in paths.items() if path.startswith(wanted_path)])

for folder_key, values in photographer_paths.items():
    path_id = values['id']
    opened_filelist = opener.open("http://assembly.galleria.fi/?type=getFileList&id=%s" % path_id)
    opened_filelist_json = opened_filelist.read()
    files = json.loads(opened_filelist_json)
    if not files:
        continue
    author = urllib.unquote_plus(folder_key.replace(wanted_path, "")).strip("/")

    if author == "":
        author = "unknown"

    known_titles = set()
    for image_path, image_data in sorted(files.items(), lambda x, y: cmp(x[0], y[0])):
        image_name = image_path.replace(folder_key, "")
        title = urllib.unquote_plus(image_name)
        next_id = 2
        new_title = title
        while new_title.lower() in known_titles:
            new_title = "%s-%d" % (title, next_id)
            next_id += 1
        title = new_title
        known_titles.add(title.lower())
        filename = asmmetadata.normalize_key(
            "%s by %s" % (title, author)) + ".jpeg"
        print_shell(
            "wget -nc --no-host '%s://%s%s?img=full' -O '%s'/%s" % (
                parsed_url.scheme,
                parsed_url.netloc,
                image_path,
                args.photos_root,
                filename))
        image_file = "%s/%s" % (photo_category, filename)
        print_metadata("author:%s|title:%s|galleriafi:%s|image-file:%s" % (
                author.encode("utf-8"),
                title.encode("utf-8"),
                image_path.encode("utf-8"),
                image_file.encode("utf-8")))
