#!/usr/bin/env python

import argparse
import asmmetadata
import base64
import cgi
import os.path
import sys
import time
from xml.sax.saxutils import escape
from xml.sax.saxutils import quoteattr

CURRENT_TIME = time.strftime("%Y-%m-%d %H:%M:%S")

parser = argparse.ArgumentParser()
parser.add_argument("files_root", metavar="files-root")
parser.add_argument("--no-empty", dest="noempty", action="store_true",
                  help="Prevent empty sections from going to import data.")

args = parser.parse_args()
FILEROOT = args.files_root

create_empty_sections = not args.noempty

def display_asset(path, title, data):
    return """
  <asset path="%(path)s">
    <edition parameters="lang: workflow:public"
         title=%(title)s
         tags=""
         created="2011-02-11 10:00:00"
         modified="2011-02-11 10:00:00"><![CDATA[%(data)s
]]></edition>
  </asset>
""" % {'path': path,
       'title': quoteattr(title),
       'data': base64.encodestring(data),
       }

def select_smaller_thumbnail(fileprefix):
    thumbnail_jpeg = open(fileprefix + ".jpeg", "r").read()
    thumbnail_png = open(fileprefix + ".png", "r").read()

    if len(thumbnail_jpeg) < len(thumbnail_png):
        return thumbnail_jpeg, '.jpeg'
    else:
        return thumbnail_png, '.png'

entry_data = asmmetadata.parse_file(sys.stdin)

print """<?xml version="1.0" encoding="utf-8"?>
<import base="http://archive.assembly.org">
  <mediagallery path="%(year)s" purge="true">
    <edition parameters="lang: workflow:public"
         title="%(year)s"
         tags=""
         created="2011-02-11 10:00:00"
         modified="2011-02-11 10:00:00">
    </edition>
  </mediagallery>
""" % {'year': entry_data.year}

def print_section(year, section):
    normalized_section = section['key']
    sectionpath = "%s/%s" % (year, normalized_section)
    additionalinfo = ''
    description = ''
    if 'description' in section:
        description += section['description']
        # XXX Check for next year.
        # if section['ongoing'] is True:
        #     pms_path = "asm11/compos/%s/vote/" % section['pms-category']
        #     description += "<p>You can vote these entries at <a href='https://pms.asm.fi/%s'>PMS</a>!</p>" % pms_path
    if 'youtube-playlist' in section:
        description += """<p><a href="http://www.youtube.com/playlist?list=%s">Youtube playlist of these entries</a></p>""" % section['youtube-playlist']

    if description != '':
        additionalinfo = """
<mediagalleryadditionalinfo
    description=%s
>
</mediagalleryadditionalinfo>
""" % quoteattr(description)

    section_unicode = """
  <mediagallery path="%(sectionpath)s">
    <edition parameters="lang: workflow:public"
         title="%(section)s"
         tags=""
         created="2011-02-11 10:00:00"
         modified="2011-02-11 10:00:00">
        %(additionalinfo)s
    </edition>
  </mediagallery>
""" % {'year': year,
       'section': section['name'],
       'normalizedsection': normalized_section,
       'sectionpath': sectionpath,
       'additionalinfo': additionalinfo,
       }

    print section_unicode.encode("utf-8")

def get_ordinal_suffix(number):
    suffixes = {1: 'st',
               2: 'nd',
               3: 'rd'}
    suffix = suffixes.get(number % 10, 'th')
    if number in [11, 12, 13]:
        suffix = 'th'
    return suffix

def get_thumbnail_data(entry):
    thumbnail_base = asmmetadata.select_thumbnail_base(entry)
    thumbnail = None
    if thumbnail_base is not None:
        thumbnail, _ = select_smaller_thumbnail(os.path.join(FILEROOT, thumbnail_base))
    else:
        # We don't have any displayable data.
        return None

    if thumbnail is None:
        del entry['section']
        sys.stderr.write("Missing thumbnail for %s!\n" % str(entry))
        sys.exit(1)

    return thumbnail

def print_entry(year, entry):
    title = entry['title']
    author = entry['author']
    section_name = entry['section']['name']
    if "AssemblyTV" in section_name or "Seminars" in section_name or "Winter" in section_name:
        name = title
    else:
        name = "%s by %s" % (title, author)

    normalized_name = asmmetadata.normalize_key(name)
    normalized_section = asmmetadata.normalize_key(section_name)
    position = entry.get('position', 0)

    extra_assets = ""

    locations = ""

    description = u""
    if 'warning' in entry:
        description += u"%s</p>\n<p>" % cgi.escape(entry['warning'])

    position_str = None

    if position != 0:
        position_str = str(position) + get_ordinal_suffix(position) + " place"

    has_media = False

    display_author = None
    if "Misc" in section_name or "Photos" in section_name:
        pass
    elif not "AssemblyTV" in section_name and not "Winter" in section_name:
        display_author = author
        if not "Seminars" in section_name:
            if entry['section'].get('ongoing', False) is False:
                if position_str is not None:
                    description += u"%s" % position_str
                else:
                    description += u"Not qualified to be shown on the big screen"
                description += u".</p>\n<p>\n"
            # XXX Check for next year.
            # else:
            #     pms_path = "asm11/compos/%s/vote/" % entry['section']['pms-category']
            #     description += "<p>You can vote this entry at <a href='https://pms.asm.fi/%s'>PMS</a>!</p>" % pms_path

    if 'description' in entry:
        description += u"%s</p>\n<p>" % cgi.escape(entry['description'])

    if 'platform' in entry:
        description += u"Platform: %s</p>\n<p>" % cgi.escape(entry['platform'])

    if 'techniques' in entry:
        description += u"Notes: %s</p>\n<p>" % cgi.escape(entry['techniques'])

    if display_author is not None:
        description += u"Author: %s\n" % cgi.escape(display_author)

    # Youtube is our primary location
    if 'youtube' in entry:
        has_media = True
        youtube = entry['youtube']
        locations += "<location type='youtube'>%s</location>" % youtube

    # Youtube is primary location
    if 'dtv' in entry:
        has_media = True
        demoscenetv = entry['dtv']
        locations += "<location type='demoscenetv'>%s</location>" % (escape(demoscenetv))

    # XXX prevent the creation of humongous files.
    if 'galleriafi' in entry:
        return

    if ('image-file' in entry or 'galleriafi' in entry) and 'webfile' not in entry:
        image_file = entry.get('image-file')
        if image_file is None:
            image_file = "%s/%s.jpeg" % (normalized_section, normalized_name)
        if image_file.endswith(".png") or image_file.endswith(".jpeg") or image_file.endswith(".gif"):
            has_media = True
            baseprefix, _ = image_file.split(".")
            viewfile, postfix = select_smaller_thumbnail(os.path.join(FILEROOT, 'thumbnails/large/%s' % baseprefix))

            normal_prefix = asmmetadata.normalize_key(baseprefix)
            image_filename = normal_prefix + postfix
            locations += "<location type='image'>%s|%s</location>" % (image_filename, escape(name))

            extra_assets += display_asset(
                "%d/%s/%s/%s" % (year, normalized_section, normalized_name, image_filename), name, viewfile)

    if 'webfile' in entry:
        webfile = entry['webfile']
        if webfile.endswith(".png") or webfile.endswith(".jpeg") or webfile.endswith(".gif"):
            has_media = True
            baseprefix, _ = webfile.split(".")
            viewfile, postfix = select_smaller_thumbnail(os.path.join(FILEROOT, 'thumbnails/large/%s' % baseprefix))

            normal_prefix = asmmetadata.normalize_key(baseprefix)
            image_filename = normal_prefix + postfix
            locations += "<location type='download'>http://media.assembly.org/compo-media/assembly%d/%s|Full resolution</location>" % (year, webfile)
            locations += "<location type='image'>%s|%s</location>" % (image_filename, escape(name))

            extra_assets += display_asset(
                "%d/%s/%s/%s" % (year, normalized_section, normalized_name, image_filename), name, viewfile)
        elif webfile.endswith(".mp3"):
            locations += "<location type='download'>http://media.assembly.org/compo-media/assembly%d/%s|MP3</location>" % (year, webfile)

    if 'pouet' in entry:
        pouet = entry['pouet']
        locations += "<location type='pouet'>%s</location>" % (pouet)

    if 'download' in entry:
        download = entry['download']
        download_type = "Original"
        if "game" in section_name.lower():
            download_type = "Playable game"
        locations += "<location type='download'>%s|%s</location>" % (escape(download), download_type)

    if 'sceneorg' in entry:
        sceneorg = entry['sceneorg']
        download_type = "Original"
        if "game" in section_name.lower():
            download_type = "Playable game"
        if ";" in sceneorg:
            parts = sceneorg.split(";")
            i = 1
            for part in parts:
                locations += "<location type='sceneorg'>%s|%s (%d/%d)</location>" % (
                    escape(part), download_type, i, len(parts))
                i += 1
        else:
            locations += "<location type='sceneorg'>%s|%s</location>" % (escape(sceneorg), download_type)

    if 'sceneorgvideo' in entry:
        sceneorgvideo = entry['sceneorgvideo']
        locations += "<location type='sceneorg'>%s|HQ video</location>" % (escape(sceneorgvideo))
    elif 'media' in entry:
        mediavideo = entry['media']
        locations += "<location type='download'>http://media.assembly.org%s|HQ video</location>" % (mediavideo)

    if "galleriafi" in entry:
        locations += "<location type='download'>http://assembly.galleria.fi%s|Original image</location>" % (entry["galleriafi"])


    if not has_media:
        return

    has_thumbnail = False
    if entry.get('use-parent-thumbnail', False) is True:
        has_thumbnail = True
    else:
        thumbnail_data = get_thumbnail_data(entry)
        if thumbnail_data is not None:
            has_thumbnail = True

    if not has_thumbnail:
        return

    ranking = 'ranking="%d"' % position
    if position == 0:
        ranking = ''

    description_non_unicode = description

    tags = set()
    if 'tags' in entry:
        tags.update(entry['tags'].split(" "))

    if entry.get('use-parent-thumbnail', False) is False:
        thumbnail_asset = """
  <asset path="%(year)s/%(normalizedsection)s/%(normalizedname)s/thumbnail">
    <edition parameters="lang: workflow:public"
         title=%(title)s
         tags="hide-search"
         created="%(current-time)s"
         modified="%(current-time)s"><![CDATA[%(data)s
]]></edition>
  </asset>
""" % {'year': year,
       'normalizedsection': normalized_section,
       'normalizedname': normalized_name,
       'data': base64.encodestring(thumbnail_data),
       'title': quoteattr(title),
       'current-time': CURRENT_TIME,
       }
    else:
        thumbnail_asset = ''

    asset_data = """
  <externalasset path="%(year)s/%(normalizedsection)s/%(normalizedname)s">
    <edition parameters="lang: workflow:public"
         title=%(title)s
         tags=%(tags)s
         created="%(current-time)s"
         modified="%(current-time)s">
      <mediagalleryadditionalinfo
          author=%(author)s
          description=%(description)s
          %(ranking)s></mediagalleryadditionalinfo>
      %(locations)s
    </edition>
  </externalasset>
%(thumbnail)s
""" % {'year': year,
       'normalizedsection': normalized_section,
       'normalizedname': normalized_name,
       'title': quoteattr(title),
       'author': quoteattr(author),
       'ranking': ranking,
       'thumbnail': thumbnail_asset,
       'locations': locations,
       'description': quoteattr(description_non_unicode),
       'current-time': CURRENT_TIME,
       'tags': quoteattr(" ".join(tags)),
       }
    asset_data_str = asset_data.encode("utf-8")
    print asset_data_str
    extra_assets_str = extra_assets.encode("utf-8")
    print extra_assets_str


music_thumbnail, _ = select_smaller_thumbnail(
    os.path.join(FILEROOT, 'thumbnails', 'music-thumbnail'))
music_thumbnail_asset = """
<asset path="%(year)s/music-thumbnail">
  <edition parameters="lang: workflow:public"
         title="Music thumbnail for %(year)s"
         tags="hide-navigation hide-search"
         created="%(current-time)s"
         modified="%(current-time)s"><![CDATA[%(data)s
]]></edition>
  </asset>
""" % {'year': entry_data.year,
       'data': base64.encodestring(music_thumbnail),
       'current-time': CURRENT_TIME,
}
asset_data_str = music_thumbnail_asset.encode("utf-8")
print asset_data_str

for section in entry_data.sections:
    if section.get('public', True) is False:
        continue
    if len(section['entries']) == 0 and not create_empty_sections:
        continue
    print_section(entry_data.year, section)

    sorted_entries = asmmetadata.sort_entries(section['entries'])

    # Music files have all the same thumbnail.
    if 'music' in section['name'].lower():
        for entry in sorted_entries:
            entry['use-parent-thumbnail'] = True

    for entry in sorted_entries:
        print_entry(entry_data.year, entry)

print """</import>"""
