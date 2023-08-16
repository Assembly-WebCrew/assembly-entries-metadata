#!/usr/bin/env python3

import argparse
import asmmetadata
import logging
import os
import os.path
import requests
from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument("datafile")
parser.add_argument("dataroot")
args = parser.parse_args()

entry_data = asmmetadata.parse_file(open(args.datafile))
folder_data = requests.get("https://assembly.galleria.fi/?type=getFolderTree").json()

for section in entry_data.sections:
    galleriafi_prefix = section.get('galleriafi')
    if galleriafi_prefix is None:
        continue
    photos_category = section["name"].replace("Photos", "")
    photos_category = photos_category.replace(" ", "")
    photos_dir = "photos-%s" % photos_category
    if photos_category == "":
        photos_dir = "photos"
    photos_path = os.path.join(args.dataroot, photos_dir)

    galleriafi_folders = []
    for x in sorted(folder_data.keys(), key=lambda x: x.lower()):
        if not x.startswith(galleriafi_prefix):
            continue
        galleriafi_folders.append(x)
    if len(galleriafi_folders) == 0:
        continue
    if not os.path.exists(photos_path):
        os.makedirs(photos_path)
    section_images = []
    for galleriafi_folder in galleriafi_folders:
        #     data_url =
        # "https://assembly.galleria.fi/?type=getFileList&id=%s" %
        # urllib.parse.quote_plus(galleriafi_folder)
        data_url = "https://assembly.galleria.fi/?type=getFileListJSON"
        images = requests.post(
            data_url,
            data={"ajaxresponse": 1, "folder": galleriafi_folder},
        ).json()
        for image in images["message"]:
            galleriafi_path = image["filepath"]
            image_filename = asmmetadata.get_galleriafi_filename(
                galleriafi_path)
            #title = path_parts[-1]
            image_dir_filename = os.path.join(photos_dir, image_filename)
            image_path = os.path.join(photos_path, image_filename)
            if not os.path.exists(image_path) or os.stat(image_path).st_size == 0:
                download_url = (
                    "https://assembly.galleria.fi%s?img=full" % galleriafi_path)
                print("Downloading %s" % download_url)
                tmp_file = image_path + ".tmp"
                image_response = requests.get(download_url, headers={'user-agent': 'my-app/0.0.1'})
                data = image_response.content
                if len(data) == 0:
                    raise RuntimeError(
                        "Zero length data received from %s" % download_url)
                with open(tmp_file, "wb") as target_fp:
                    target_fp.write(data)
                os.rename(tmp_file, image_path)
            section_images.append(galleriafi_path)

    section_entries = []
    known_paths = {}
    for entry in section["entries"]:
        known_paths[entry["galleriafi"]] = entry
    changed_entries = []
    for galleriafi_path in section_images:
        add_entry = None
        if galleriafi_path in known_paths:
            add_entry = known_paths[galleriafi_path]
        else:
            path_parts = galleriafi_path.split("/")
            author = path_parts[-2]
            title = path_parts[-1]
            add_entry = {
                "author": author,
                "galleriafi": galleriafi_path,
                "title": title,
                "section": section,
            }
        changed_entries.append(add_entry)
    section["entries"] = changed_entries

asmmetadata.print_metadata(open(args.datafile, "w"), entry_data)

# paths = json.loads(data)
# photographer_paths = dict([
#         (path, data) for path, data in paths.items() if path.startswith(wanted_path)])

# for folder_key, values in photographer_paths.items():
#     path_id = values['id']
#     opened_filelist = opener.open(
#     opened_filelist_json = opened_filelist.read()
#     files = json.loads(opened_filelist_json)
#     if not files:
#         continue
#     author = urllib.unquote_plus(folder_key.replace(wanted_path, "")).strip("/")

#     if author == "":
#         author = "unknown"

#     known_titles = set()
#     for image_path, image_data in sorted(files.items(), lambda x, y: cmp(x[0], y[0])):
#         image_name = image_path.replace(folder_key, "")
#         title = urllib.unquote_plus(image_name)
#         next_id = 2
#         new_title = title
#         while new_title.lower() in known_titles:
#             new_title = "%s-%d" % (title, next_id)
#             next_id += 1
#         title = new_title
#         known_titles.add(title.lower())
#         filename = asmmetadata.normalize_key(
#             "%s by %s" % (title, author)) + ".jpeg"
#         print_shell(
#             "wget -nc --no-host '%s://%s%s?img=full' -O '%s'/%s" % (
#                 parsed_url.scheme,
#                 parsed_url.netloc,
#                 image_path,
#                 args.photos_root,
#                 filename))
#         image_file = "%s/%s" % (photo_category, filename)
#         print_metadata("author:%s|title:%s|galleriafi:%s|image-file:%s" % (
#                 author,
#                 title,
#                 image_path,
#                 image_file))
