# -*- coding: utf-8 -*-

import cgi
import dateutil.parser
import hashlib
import re
import unicodedata
import urllib


YOUTUBE_MAX_TITLE_LENGTH = 100


def is_image(filename):
    return re.match(r".+\.(png|jpg|jpeg|gif|tiff)$", filename, re.IGNORECASE)


def get_party_name(year, section_name):
    if year < 2007:
        return u"Assembly %d" % year
    elif 'winter' in section_name.lower():
        return u"Assembly Winter %d" % year
    else:
        return u"Assembly Summer %d" % year


def get_party_tags(year, section_name):
    tags = []
    if year < 2007:
        tags.extend(["assembly", str(year), "asm%02d" % (year % 100), "Assembly %d" % year])
    elif 'winter' in section_name.lower():
        tags.extend(["assembly", str(year), "asm%02d" % (year % 100), "asmw%02d" % (year % 100), "Assembly Winter %d" % year])
    else:
        tags.extend(["assembly", str(year), "asm%02d" % (year % 100), "asms%02d" % (year % 100), "Assembly Summer %d" % year])
    if year == 2000:
        tags.append("asm2k")
    return tags


def get_entry_name(entry):
    title = entry['title']
    author = entry['author']
    if entry["section"].get("author-in-title", True):
        name = u"%s by %s" % (title, author)
    else:
        name = title
    return name


def get_content_types(section_name):
    normalized_section_name = normalize_key(section_name)

    # Major non-computer generated recordings.
    if "seminar" in normalized_section_name:
        return set(["seminar", "summer"])
    if "assemblytv" in normalized_section_name:
        return set(["assemblytv", "summer"])
    if "winter" in normalized_section_name:
        return set(["assemblytv", "winter"])
    # Don't separate photo sections yet.
    if "photo" in normalized_section_name:
        return set(["photo", "winter", "summer"])
    # Everything else is done during the summer.
    types = ["summer"]

    # Realtime types.
    if re.search("(^| )4k", normalized_section_name):
         types.extend(["4k", "intro", "realtime", "demo-product"])
    if re.search("(^| )64k", normalized_section_name):
         types.extend(["64k", "intro", "realtime", "demo-product"])
    if re.search("(^| )40k", normalized_section_name):
         types.extend(["40k", "intro", "realtime", "demo-product"])
    if "intro" in normalized_section_name:
         types.extend(["intro", "realtime", "demo-product"])
    if "demo" in normalized_section_name:
         types.extend(["demo", "realtime", "demo-product"])

    # Different platforms.
    if "c64" in normalized_section_name:
        types.extend(["c64"])
    if "amiga" in normalized_section_name:
         types.extend(["amiga"])
    if "console" in normalized_section_name:
         types.extend(["console"])
    if "java" in normalized_section_name:
         types.extend(["java"])
    if "win95" in normalized_section_name:
         types.extend(["win95", "windows"])
    if "windows" in normalized_section_name:
         types.extend(["windows"])
    if "oldskool" in normalized_section_name:
         types.extend(["oldskool"])
    if "mobile" in normalized_section_name:
         types.extend(["mobile"])
    if "browser" in normalized_section_name:
         types.extend(["browser"])
    if "flash" in normalized_section_name:
         types.extend(["flash"])
    if "winamp" in normalized_section_name:
         types.extend(["winamp"])
    if "playstation" in normalized_section_name:
         types.extend(["playstation"])

    # Music
    if "channel" in normalized_section_name:
         types.extend(["tracker"])
    if "tiny" in normalized_section_name:
         types.extend(["tracker"])
    if "music" in normalized_section_name:
         types.extend(["music"])
    if re.match("^music$", normalized_section_name):
         types.extend(["music-any"])
    if "mp3" in normalized_section_name:
         types.extend(["mp3", "music-any"])
    if "instrumental" in normalized_section_name:
         types.extend(["instrumental"])

    # Different video types.
    if "animation" in normalized_section_name:
         types.extend(["animation", "video"])
    if re.match("^wild$", normalized_section_name):
         types.extend(["video", "platform-any"])
    if "film" in normalized_section_name:
         types.extend(["video", "platform-any"])

    # Graphics.
    if "graphics" in normalized_section_name:
         types.extend(["graphics"])
    if "raytrace" in normalized_section_name:
         types.extend(["raytrace"])
    if "ansi" in normalized_section_name:
        types.extend(["ansi"])
    if "themed" in normalized_section_name:
        types.extend(["themed"])
    if "analog" in normalized_section_name:
         types.extend(["analog", "drawn"])
    if "drawn" in normalized_section_name:
         types.extend(["drawn"])
    if "pixel graphics" in normalized_section_name:
         types.extend(["drawn"])

    # Miscellaneous.
    if "fast" in normalized_section_name:
        types.extend(["fast", "themed"])
    if "extreme" in normalized_section_name:
         types.extend(["extreme"])
    if "executable" in normalized_section_name:
         types.extend(["extreme"])
    if "wild" in normalized_section_name:
         types.extend(["wild", "platform-any"])
    if "game" in normalized_section_name:
         types.extend(["gamedev"])

    return set(types)


def get_long_section_name(section):
    if "winter" in section["name"].lower():
        return u"AssemblyTV"
    elif "assemblytv" in section["name"].lower():
        return u"AssemblyTV"
    elif not section.get("ranked", True):
        return section["name"]
    else:
        return u"%s competition" % section["name"]


def normalize_key(value):
    normalized = value.strip().lower()
    normalized = unicodedata.normalize('NFKC', normalized)
    normalized = normalized.replace(u"ä", u"a")
    normalized = normalized.replace(u"ö", u"o")
    normalized = normalized.replace(u"å", u"a")
    normalized = re.sub("[^a-z0-9]", "-", normalized)
    normalized = re.sub("-{2,}", "-", normalized)
    normalized = normalized.strip("-")
    return normalized


def get_entry_key(entry):
    return normalize_key(u"%s-by-%s" % (entry['title'], entry['author']))


class EntryYear(object):
    year = None

    def __init__(self):
        self.sections = []
        self.entries = []

    def getSection(self, name):
        for section in self.sections:
            if section['key'] == normalize_key(name):
                return section
        return None

    def createSection(self, name):
        if not self.getSection(name) is None:
            return self.getSection(name)
        section = {
                'key': normalize_key(name),
                'name': name,
                'year': self.year,
                'entries': [],
                }
        self.sections.append(section)
        return section

    def addEntry(self, section, entryData):
        entryData['section'] = section
        section['entries'].append(entryData)
        self.entries.append(entryData)

    def findEntry(self, field, value):
        assert value is not None
        for entry in self.entries:
            if entry.get(field) == value:
                return entry
        return None


def parse_entry_line(line):
    try:
        data_dict = dict(
            (str(x.split(":", 1)[0]),
             unescape_value(x.split(":", 1)[1])) for x in line.split("|"))
    except:
        print line
        raise

    position = int(data_dict.get('position', u'0'))
    if position != 0:
        data_dict['position'] = position
    elif 'position' in data_dict:
        del data_dict['position']

    if 'media' in data_dict and not 'guid' in data_dict:
        if re.match("^/vod/\d+/[^/]+/(\d+)_.+", data_dict['media']):
            guid = re.sub("/vod/\d+/[^/]+/(\d+)_.+", "\\1", data_dict['media'])
            data_dict['guid'] = guid

    return data_dict


def parse_file(file_handle):
    result = EntryYear()

    year = None
    section = None

    known_keys = set()
    for line in file_handle:
        line = unicode(line.strip(), "utf-8")
        if line == "":
            continue
        if line[0] == "#":
            continue
        if line[0] == ":":
            try:
                data_type, value = line.strip().split(" ", 1)
            except ValueError:
                print("Invalid line: %s" % line.strip())
                raise
            if data_type == ":year":
                assert result.year is None
                year = int(value)
                result.year = year
            elif data_type == ":section":
                # Sections must have year.
                assert year is not None
                section_name = value
                assert result.getSection(section_name) is None, "Section %s was defined for the second time." % section_name
                section = result.createSection(section_name)
            elif data_type == ":description":
                # Descriptions can only be under section.
                assert section is not None
                # Only one description per section is allowed.
                assert 'description' not in section
                if len(value):
                    section['description'] = value
            elif data_type == ":youtube-playlist":
                assert section is not None
                assert 'youtube-playlist' not in section
                section['youtube-playlist'] = value
            elif data_type == ":pms-category":
                # Categories can only be under section.
                assert section is not None
                # Only one category per section is allowed.
                assert 'pms-category' not in section
                if len(value):
                    section['pms-category'] = value
            elif data_type == ":ongoing":
                if value.lower() == "true":
                    section['ongoing'] = True
            elif data_type == ":public":
                if value.lower() == "false":
                    section['public'] = False
            elif data_type == ":public-after":
                section['public-after'] = dateutil.parser.parse(value)
            elif data_type == ":sceneorg":
                section['sceneorg'] = value
            elif data_type == ":galleriafi":
                section['galleriafi'] = value
            elif data_type == ":elaine-category":
                # Categories can only be under section.
                assert section is not None
                # Only one elaine category per section is allowed.
                assert 'elaine-category' not in section
                if len(value):
                    section['elaine-category'] = value
            elif data_type == ":ranked":
                # By default sections are ranked as they mostly
                # represent demoscene competition results.
                if value.lower() == "false":
                    section['ranked'] = False
                else:
                    section['ranked'] = True
            elif data_type == ":author-in-title":
                # By default authors are part of the title in form of:
                # <name> by <author>
                #
                # Only some specific categories, like AssemblyTV,
                # eSports, and Winter can get without displaying the
                # author in the title.
                if value.lower() == "false":
                    section["author-in-title"] = False
                else:
                    section["author-in-title"] = True
            else:
                raise RuntimeError, "Unknown type %s." % data_type
            continue

        assert year is not None
        assert section is not None

        data_dict = parse_entry_line(line)

        assert 'section' not in data_dict
        if get_entry_key(data_dict) in known_keys:
            raise ValueError("Entry %s has a duplicate key" % data_dict)
        known_keys.add(get_entry_key(data_dict))

        result.addEntry(section, data_dict)

    return result


def unescape_value(value):
    return value.replace("&#124;", "|")


def escape_value(value):
    return value.replace("|", "&#124;")


def get_archive_link_entry(entry):
    key = get_entry_key(entry)
    return u"http://archive.assembly.org/%d/%s/%s" % (
        entry["section"]["year"], entry["section"]["key"], key)


def print_metadata(outfile, year_entry_data):
    outfile.write(":year %d\n" % year_entry_data.year)
    for section in year_entry_data.sections:
        outfile.write("\n:section %s\n" % section['name'])
        if 'ranked' in section:
            ranked_text = "true"
            if section["ranked"] is False:
                ranked_text = "false"
            outfile.write(":ranked %s\n" % ranked_text)
        if 'author-in-title' in section:
            author_in_title_text = "true"
            if section["author-in-title"] is False:
                author_in_title_text = "false"
            outfile.write(":author-in-title %s\n" % author_in_title_text)
        if 'galleriafi' in section:
            outfile.write(":galleriafi %s\n" % section['galleriafi'])
        if 'youtube-playlist' in section:
            outfile.write(
                ":youtube-playlist %s\n" % section['youtube-playlist'].encode("utf-8"))
        if 'pms-category' in section:
            outfile.write(":pms-category %s\n" % section['pms-category'])
        if 'elaine-category' in section:
            outfile.write(":elaine-category %s\n" % section['elaine-category'])
        if 'description' in section:
            outfile.write(
                ":description %s\n" % section['description'].encode("utf-8"))
        if 'sceneorg' in section:
            outfile.write(
                ":sceneorg %s\n" % section['sceneorg'].encode("utf-8"))
        if 'ongoing' in section:
            ongoing_text = "false"
            if section['ongoing'] is True:
                ongoing_text = "true"
            outfile.write(":ongoing %s\n" % ongoing_text)
        if 'public' in section:
            public_text = "true"
            if section['public'] is False:
                public_text = "false"
            outfile.write(":public %s\n" % public_text)
        if 'public-after' in section:
            public_after_text = section['public-after'].strftime("%Y-%m-%d %H:%M%z")
            outfile.write(":public-after %s\n" % public_after_text)
        if 'galleriafi' in section:
            outfile.write(":galleriafi %s\n" % section['galleriafi'])

        outfile.write("\n")

        for entry in section['entries']:
            del entry['section']

            for key, value in entry.items():
                if value is None:
                    del entry[key]

            for key, value in entry.items():
                entry[key] = escape_value(u"%s" % value)

            parts = sorted(
                u"%s:%s" % (key, value) for key, value in entry.items())
            outline = u"|".join(parts)
            outfile.write("%s\n" % outline.encode("utf-8"))

        outfile.write("\n")


def sort_entries(entries):
    return sorted(
        entries,
        lambda x, y: cmp(x.get('position', 999), y.get('position', 999)))


def select_thumbnail_base(entry):
    if 'youtube' in entry:
        return 'youtube-thumbnails/%s' % entry['youtube']
    if 'dtv' in entry:
        demoscenetv_thumb = cgi.parse_qs(entry['dtv'])['image'][0].split("/")[-1].split(".")[0]
        return 'dtv-thumbnails/%s' % demoscenetv_thumb
    if 'webfile' in entry or 'image-file' in entry or 'galleriafi' in entry:
        filename = entry.get('webfile') or entry.get('image-file')
        if filename is None:
            filename = "%s/%s-by-%s.jpeg" % (normalize_key(entry['section']['name']), normalize_key(entry['title']), normalize_key(entry['author']))
        baseprefix, _ = filename.split(".")
        if is_image(filename):
            return 'thumbnails/small/%s' % baseprefix
    return None


def create_merged_image_base(start, entries):
    merged_name = "|".join(
        map(normalize_key,
            map(lambda entry: "%s-by-%s" % (entry['title'], entry['author']),
                entries)))
    filenames_digest = hashlib.md5(merged_name).hexdigest()
    return "merged-%s-%02d-%02d-%s" % (
        entries[0]['section']['key'],
        start,
        start + len(entries) - 1,
        filenames_digest,
        )


def get_ordinal_suffix(number):
    suffixes = {
        1: 'st',
        2: 'nd',
        3: 'rd'}
    suffix = suffixes.get(number % 10, 'th')
    if number in [11, 12, 13]:
        suffix = 'th'
    return suffix


def get_youtube_info_data(entry):
    title = entry['title']
    author = entry['author']
    section_name = entry['section']['name']
    name = get_entry_name(entry)

    position = entry.get('position', 0)

    description = u""
    if 'warning' in entry:
        description += u"%s\n\n" % entry['warning']

    position_str = None

    if entry["section"].get("ranked", True):
        if position != 0:
            position_str = str(position) + get_ordinal_suffix(position) + " place"

    party_name = get_party_name(
        entry['section']['year'], entry['section']['name'])

    display_author = None
    if "Misc" in section_name or "Photos" in section_name:
        pass
    elif not "AssemblyTV" in section_name and not "Winter" in section_name:
        display_author = author
        if entry["section"].get("ranked", True):
            description += "%s %s competition entry" % (party_name, section_name)
            if entry['section'].get('ongoing', False) is False:
                if position_str is not None:
                    description += u", %s" % position_str
                else:
                    description += u", not qualified to be shown on the big screen"
            description += u".\n\n"
        elif "Seminars" in section_name:
            description += u"%s seminar presentation.\n\n" % party_name
    elif "AssemblyTV" in section_name or "Winter" in section_name:
        description += u"%s AssemblyTV program.\n\n" % party_name

    if 'description' in entry:
        description += u"%s\n\n" % entry['description']

    if 'platform' in entry:
        description += u"Platform: %s\n" % entry['platform']

    if 'techniques' in entry:
        description += u"Notes: %s\n" % entry['techniques']

    description += u"Title: %s\n" % title
    if display_author is not None:
        description += u"Author: %s\n" % display_author

    newlined = False

    pouet = entry.get('pouet', None)
    if pouet is not None:
        if not newlined:
            description += u"\n"
            newlined = True
        description += u"Pouet.net: http://pouet.net/prod.php?which=%s\n" % urllib.quote_plus(pouet.strip())

    if 'download' in entry:
        if not newlined:
            description += u"\n"
            newlined = True
        download = entry['download']
        download_type = "Download original:"
        if "game" in section_name.lower():
            download_type = "Download playable game:"
        description += "%s: %s\n" % (download_type, download)

    if 'sceneorg' in entry:
        if not newlined:
            description += u"\n"
            newlined = True
        sceneorg = entry['sceneorg']
        download_type = "original"
        if "game" in section_name.lower():
            download_type = "playable game"
        if "," in sceneorg:
            parts = sceneorg.split(",")
            i = 1
            for part in parts:
                description += "Download %s part %d/%d: http://www.scene.org/file.php?file=%s\n" % (
                    download_type, i, len(parts), urllib.quote_plus(part))
                i += 1
        else:
            description += "Download %s: http://www.scene.org/file.php?file=%s\n" % (
                download_type, urllib.quote_plus(sceneorg))

    if 'sceneorgvideo' in entry:
        if not newlined:
            description += u"\n"
            newlined = True
        sceneorgvideo = entry['sceneorgvideo']
        description += "Download high quality video: http://www.scene.org/file.php?file=%s\n" % urllib.quote_plus(sceneorgvideo)
    elif 'media' in entry:
        if not newlined:
            description += u"\n"
            newlined = True
        mediavideo = entry['media']
        description += "Download high quality video: http://media.assembly.org%s\n" % mediavideo

    description += u"\n"
    if "youtube-playlist" in entry["section"]:
        description += u"Youtube playlist: https://www.youtube.com/playlist?list=%s\n" % entry["section"]["youtube-playlist"]
    description += u"This entry at Assembly Archive: %s\n" % get_archive_link_entry(entry)

    tags = set(get_party_tags(
            entry['section']['year'], entry['section']['name']))

    if 'tags' in entry:
        tags.update(entry['tags'].split(" "))

    if "AssemblyTV" in entry['section']['name'] or "Winter" in entry['section']['name']:
        tags.add("AssemblyTV")
    if "Seminars" in entry['section']['name']:
        tags.add("seminar")

    description = description.replace("<", "-")
    description = description.replace(">", "-")

    name = name.replace("<", "-")
    name = name.replace(">", "-")

    category = "Entertainment"
    if "Seminars" in entry['section']['name']:
        category = "Tech"

    return {
        'title': name[:YOUTUBE_MAX_TITLE_LENGTH],
        'description': description,
        'tags': list(tags),
        'category': category,
        }


def reorder_positioned_section_entries(inout_entries):
    def _get_key(value):
        return value.get("position", 99999)
    inout_entries.sort(key=_get_key)
