#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgi
import dataclasses
import dateutil.parser
import hashlib
import re
import typing
import unicodedata
import urllib
import urllib.parse


YOUTUBE_MAX_TITLE_LENGTH = 100

Entry = typing.Dict[str, typing.Any]
Section = typing.Dict[str, typing.Any]

def is_image(filename: str) -> bool:
    match_result = re.match(
        r".+\.(png|jpg|jpeg|gif|tiff|webp)$",
        filename,
        re.IGNORECASE)
    return match_result and True or False


def get_party_name(section) -> str:
    if "party-name" in section:
        return section["party-name"]
    year = section['year']
    section_name = section['name']
    if year < 2007:
        return u"Assembly %d" % year
    elif 'winter' in section_name.lower():
        return u"Assembly Winter %d" % year
    else:
        return u"Assembly Summer %d" % year

def get_competition_name(section) -> str:
    if "compo-name" in section:
        return section["compo-name"]
    return section["name"]

def get_party_tags(year, section_name) -> typing.List[str]:
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


def get_entry_name(entry) -> str:
    title = entry['title']
    author = entry['author']
    if entry["section"].get("author-in-title", True):
        name = u"%s by %s" % (title, author)
    else:
        name = title
    return name


def get_content_types(section_name) -> typing.Set[str]:
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


def get_long_section_name(section) -> str:
    if "winter" in section["name"].lower():
        return u"AssemblyTV"
    elif "assemblytv" in section["name"].lower():
        return u"AssemblyTV"
    elif not section.get("ranked", True):
        return section["name"]
    else:
        return u"%s competition" % section["name"]


def normalize_key(value: str) -> str:
    normalized = value.strip().lower()
    normalized = unicodedata.normalize('NFKC', normalized)
    normalized = normalized.replace(u"ä", u"a")
    normalized = normalized.replace(u"ö", u"o")
    normalized = normalized.replace(u"å", u"a")
    normalized = re.sub("[^a-z0-9]", "-", normalized)
    normalized = re.sub("-{2,}", "-", normalized)
    normalized = normalized.strip("-")
    return normalized


def get_entry_key(entry) -> str:
    if not entry.get("author"):
        return normalize_key(entry["title"])
    return normalize_key(u"%s-by-%s" % (entry['title'], entry['author']))


class EntryYear(object):
    year: int = 0

    def __init__(self):
        self.sections = []
        self.entries = []

    def getSection(self, name: str) -> typing.Optional[Section]:
        for section in self.sections:
            if section['key'] == normalize_key(name):
                return section
        return None

    def createSection(self, name: str) -> Section:
        existing_section = self.getSection(name)
        if existing_section is not None:
            return existing_section
        new_section: Section = {
                'key': normalize_key(name),
                'name': name,
                'year': self.year,
                'entries': [],
                }
        self.sections.append(new_section)
        return new_section

    def addEntry(self, section: Section, entryData):
        entryData['section'] = section
        section['entries'].append(entryData)
        self.entries.append(entryData)

    def findEntry(self, field: str, value: typing.Any) -> typing.Optional[Entry]:
        assert value is not None
        for entry in self.entries:
            if entry.get(field) == value:
                return entry
        return None


def parse_entry_line(line: str) -> Entry:
    try:
        data_dict = dict(
            (str(x.split(":", 1)[0]),
             unescape_value(x.split(":", 1)[1])) for x in line.split("|"))
    except:
        print(line)
        raise

    position = int(data_dict.get('position', u'0'))
    if position != 0:
        data_dict['position'] = position  # type: ignore
    elif 'position' in data_dict:
        del data_dict['position']

    if 'media' in data_dict and not 'guid' in data_dict:
        if re.match("^/vod/\d+/[^/]+/(\d+)_.+", data_dict['media']):
            guid = re.sub("/vod/\d+/[^/]+/(\d+)_.+", "\\1", data_dict['media'])
            data_dict['guid'] = guid

    return data_dict


def parse_file(file_handle: typing.TextIO) -> EntryYear:
    result = EntryYear()

    year: typing.Optional[int] = None
    section: typing.Optional[Section] = None

    known_keys = set()
    for lineno, line in enumerate(file_handle, 1):
        line = line.strip()
        if line == "":
            continue
        if line[0] == "#":
            continue
        if line[0] == ":":
            try:
                data_type, value = line.strip().split(" ", 1)
            except ValueError:
                print("Invalid line %d: %s" % (lineno, line.strip()))
                raise
            if data_type == ":year":
                assert result.year == 0
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
            elif data_type == ":party-name":
                assert section is not None
                assert 'party-name' not in section
                section['party-name'] = value
            elif data_type == ":compo-name":
                assert section is not None
                assert 'compo-name' not in section
                section['compo-name'] = value
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
            elif data_type == ":partyman-slug":
                # Categories can only be under section.
                assert section is not None
                # Only one category per section is allowed.
                assert 'partyman-slug' not in section
                if len(value):
                    section['partyman-slug'] = value
            elif data_type == ":ongoing":
                if value.lower() == "true":
                    assert section is not None
                    section['ongoing'] = True
            elif data_type == ":public":
                if value.lower() == "false":
                    assert section is not None
                    section['public'] = False
            elif data_type == ":public-after":
                assert section is not None
                section['public-after'] = dateutil.parser.parse(value)
            elif data_type == ":sceneorg":
                assert section is not None
                section['sceneorg'] = value
            elif data_type == ":galleriafi":
                assert section is not None
                section['galleriafi'] = value
            elif data_type == ":elaine-category":
                # Categories can only be under section.
                assert section is not None
                # Only one elaine category per section is allowed.
                assert 'elaine-category' not in section
                if len(value):
                    section['elaine-category'] = value
            elif data_type == ":ranked":
                assert section is not None
                # By default sections are ranked as they mostly
                # represent demoscene competition results.
                if value.lower() == "false":
                    section['ranked'] = False
                else:
                    section['ranked'] = True
            elif data_type == ":author-in-title":
                assert section is not None
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
            elif data_type == ":manage-youtube-descriptions":
                assert section is not None
                # All kinds of eSports and AssemblyTV have author
                # added descriptions that we don't want to overwrite.
                if value.lower() == "false":
                    section['manage-youtube-descriptions'] = False
                else:
                    section['manage-youtube-descriptions'] = True
            elif data_type == ":section-thumbnail":
                assert section is not None
                assert 'section-thumbnail' not in section
                section["section-thumbnail"] = value
            else:
                raise RuntimeError("Unknown type %s." % data_type)
            continue

        assert year is not None
        assert section is not None

        data_dict = parse_entry_line(line)

        assert 'section' not in data_dict
        sectioned_key = "%s/%s" % (section["key"], get_entry_key(data_dict))
        if sectioned_key in known_keys:
            raise ValueError("Entry %s has a duplicate key" % data_dict)
        known_keys.add(sectioned_key)

        result.addEntry(section, data_dict)

    return result


def unescape_value(value: str) -> str:
    return value.replace("&#124;", "|")


def escape_value(value: str) -> str:
    return value.replace("|", "&#124;")


def get_section_archive_path(section: Section) -> str:
    return "%d/%s" % (section["year"], section["key"])


def get_archive_link_section(section: Section) -> str:
    return "https://archive.assembly.org/%s" % get_section_archive_path(section)


def get_archive_link_entry(entry: Entry) -> str:
    key = normalize_key(get_entry_name(entry))
    return "https://archive.assembly.org/%d/%s/%s" % (
        entry["section"]["year"], entry["section"]["key"], key)


def print_metadata(outfile: typing.TextIO, year_entry_data: EntryYear):
    outfile.write(":year %d\n" % year_entry_data.year)

    for section in year_entry_data.sections:
        outfile.write("\n:section %s\n" % section['name'])
        if "party-name" in section:
            outfile.write(":party-name %s\n" % section["party-name"])
        if "compo-name" in section:
            outfile.write(":compo-name %s\n" % section["compo-name"])
        if 'ranked' in section:
            ranked_text = "true"
            if section["ranked"] is False:
                ranked_text = "false"
            outfile.write(":ranked %s\n" % ranked_text)
        if 'section-thumbnail' in section:
            outfile.write(":section-thumbnail %s\n" % section["section-thumbnail"])
        if 'author-in-title' in section:
            author_in_title_text = "true"
            if section["author-in-title"] is False:
                author_in_title_text = "false"
            outfile.write(":author-in-title %s\n" % author_in_title_text)
        if 'youtube-playlist' in section:
            outfile.write(
                ":youtube-playlist %s\n" % section['youtube-playlist'])
        if 'pms-category' in section:
            outfile.write(":pms-category %s\n" % section['pms-category'])
        if 'elaine-category' in section:
            outfile.write(":elaine-category %s\n" % section['elaine-category'])
        if 'description' in section:
            outfile.write(
                ":description %s\n" % section['description'])
        if 'sceneorg' in section:
            outfile.write(":sceneorg %s\n" % section['sceneorg'])
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
        if 'manage-youtube-descriptions' in section:
            manage_text = "true"
            if section['manage-youtube-descriptions'] is False:
                manage_text = "false"
            outfile.write(":manage-youtube-descriptions %s\n" % manage_text)
        if 'partyman-slug' in section:
            outfile.write(":partyman-slug %s\n" % section['partyman-slug'])

        outfile.write("\n")

        for entry in section['entries']:
            del entry['section']

            for key, value in entry.items():
                if value is None:
                    del entry[key]

            for key, value in entry.items():
                entry[key] = escape_value("%s" % value)

            parts = sorted(
                "%s:%s" % (key, value) for key, value in entry.items())
            outline = "|".join(parts)
            outfile.write("%s\n" % outline)

        outfile.write("\n")


def sort_entries(entries):
    return sorted(
        entries,
        key=lambda x: x.get('position', 999))


def get_galleriafi_path(entry):
    pass


def get_galleriafi_filename(galleriafi_path):
    path_parts = galleriafi_path.split("/")
    image_filename = "%s-%s" % tuple(path_parts[-2:])
    return image_filename


def select_thumbnail_base(entry):
    youtube_id = get_clean_youtube_id(entry)
    if youtube_id:
        return 'youtube-thumbnails/%s' % youtube_id
    twitch_id = get_clean_twitch_id(entry)
    if twitch_id:
        return 'twitch-thumbnails/%s' % twitch_id
    if 'dtv' in entry:
        demoscenetv_thumb = cgi.parse_qs(entry['dtv'])['image'][0].split("/")[-1].split(".")[0]
        return 'dtv-thumbnails/%s' % demoscenetv_thumb
    if 'webfile' in entry or 'image-file' in entry or 'galleriafi' in entry:
        filename = entry.get('webfile') or entry.get('image-file')
        if entry.get("galleriafi"):
            normalized_section = normalize_key(entry["section"]["name"])
            filename = "%s/%s" % (
                normalized_section,
                get_galleriafi_filename(entry.get("galleriafi")))
        if filename is None:
            filename = "%s/%s-by-%s.jpeg" % (normalize_key(entry['section']['name']), normalize_key(entry['title']), normalize_key(entry['author']))
        _, baseprefix_r = filename[::-1].split(".", 1)
        baseprefix = baseprefix_r[::-1]
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


def get_youtube_timestamps_title_description(youtube_entry):
    youtube_id, _ = youtube_entry["youtube"].split("#")
    description = ""
    section = youtube_entry["section"]
    party_name = get_party_name(section)
    if section.get("ranked", True):
        description += "%s %s competition entries\n\n" % (
            party_name, section["name"])
    timestamped_entries = []
    for entry in section["entries"]:
        entry_str = ""
        list_youtube_id_timestamp = entry.get("youtube")
        if list_youtube_id_timestamp is None:
            continue
        (list_youtube_id,
         list_youtube_timestamp) = list_youtube_id_timestamp.split("#t=")
        if list_youtube_id != youtube_id:
            continue
        link_timestamp = ""
        hours = list_youtube_timestamp.split("h")
        if len(hours) == 2:
            link_timestamp += hours[0] + ":"
            minutes_str = hours[1]
        else:
            minutes_str = hours[0]
        minutes = minutes_str.split("m")
        if len(minutes) == 2:
            link_timestamp += "%02d" % (int(minutes[0])) + ":"
            seconds_str = minutes[1]
        else:
            seconds_str = minutes[0]
        if seconds_str == "":
            seconds = 0
        elif "s" not in seconds_str:
            seconds = int(seconds_str)
        else:
            seconds = int(seconds_str.rstrip("s"))
        if link_timestamp == "":
            link_timestamp = "00:%02d" % seconds
        else:
            link_timestamp += "%02d" % seconds
        entry_str += "%s %s" % (link_timestamp, get_entry_name(entry))
        if section.get("ranked", True):
            position = entry.get('position', 0)
            if position != 0:
                entry_str += " (%d%s place)" % (
                    position, get_ordinal_suffix(position))
            else:
                entry_str += " (unranked)"
        timestamped_entries.append(entry_str)
    description += "\n".join(sorted(timestamped_entries))
    description += "\n\n"
    description += "These entries at Assembly Archive: %s\n" % get_archive_link_section(section)
    description += "Event website: https://www.assembly.org/"
    title = section["name"]

    title = "%s %s" % (party_name, section["name"])
    return {"title": title, "description": description}


def get_youtube_entry_title_description(entry):
    title = entry['title']
    author = entry['author']
    section_name = entry['section']['name']
    position = entry.get('position', 0)

    description = ""
    if 'warning' in entry:
        description += "%s\n\n" % entry['warning']

    position_str = None

    if entry["section"].get("ranked", True):
        if position != 0:
            position_str = str(position) + get_ordinal_suffix(position) + " place"

    party_name = get_party_name(entry['section'])

    display_author = None
    if "Misc" in section_name or "Photos" in section_name:
        pass
    elif not "AssemblyTV" in section_name and not "Winter" in section_name:
        display_author = author
        if entry["section"].get("ranked", True):
            compo_name = get_competition_name(entry["section"])
            description += "%s %s competition entry" % (party_name, compo_name)
            if entry['section'].get('ongoing', False) is False:
                if position_str is not None:
                    description += ", %s" % position_str
                else:
                    description += ", not qualified to be shown on the big screen"
            description += ".\n\n"
        elif "Seminars" in section_name:
            description += "%s seminar presentation.\n\n" % party_name
    elif "AssemblyTV" in section_name or "Winter" in section_name:
        description += "%s AssemblyTV program.\n\n" % party_name

    if 'description' in entry:
        description += "%s\n\n" % entry['description']

    if 'platform' in entry:
        description += "Platform: %s\n" % entry['platform']

    if 'techniques' in entry:
        description += "Notes: %s\n" % entry['techniques']

    description += "Title: %s\n" % title
    if display_author is not None:
        description += "Author: %s\n" % display_author

    newlined = False

    pouet = entry.get('pouet', None)
    if pouet is not None:
        if not newlined:
            description += u"\n"
            newlined = True
        description += u"Pouet.net: http://pouet.net/prod.php?which=%s\n" % urllib.parse.quote_plus(pouet.strip())

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
                description += u"Download %s part %d/%d: https://files.scene.org/view%s\n" % (
                    download_type, i, len(parts), part)
                i += 1
        else:
            description += u"Download %s: https://files.scene.org/view%s\n" % (
                download_type, sceneorg)

    if 'sceneorgvideo' in entry:
        if not newlined:
            description += u"\n"
            newlined = True
        sceneorgvideo = entry['sceneorgvideo']
        description += "Download high quality video: https://files.scene.org/view%s\n" % sceneorgvideo
    elif 'media' in entry:
        if not newlined:
            description += u"\n"
            newlined = True
        mediavideo = entry['media']
        description += "Download high quality video: https://media.assembly.org%s\n" % mediavideo

    description += u"\n"
    if "youtube-playlist" in entry["section"]:
        description += "Youtube playlist: https://www.youtube.com/playlist?list=%s\n" % entry["section"]["youtube-playlist"]
    description += "This entry at Assembly Archive: %s\n" % get_archive_link_entry(entry)
    description += "Event website: https://www.assembly.org/\n"
    return {"title": get_entry_name(entry), "description": description}


def get_youtube_metadata(entry):
    tags = set(get_party_tags(
            entry['section']['year'], entry['section']['name']))

    if 'tags' in entry:
        tags.update(entry['tags'].split(" "))

    tags = set(get_party_tags(
            entry['section']['year'], entry['section']['name']))

    if 'tags' in entry:
        tags.update(entry['tags'].split(" "))

    if "AssemblyTV" in entry['section']['name'] or "Winter" in entry['section']['name']:
        tags.add("AssemblyTV")
    if "Seminars" in entry['section']['name']:
        tags.add("seminar")

    category = "Entertainment"
    if "Seminars" in entry['section']['name']:
        category = "Tech"

    return {"tags": tags, "category": category}


@dataclasses.dataclass
class YoutubeInfo:
    title: str
    description: str
    tags: typing.List[str]
    category: str


def get_youtube_info_data(entry: Entry) -> YoutubeInfo:
    # Special handling for things that have timestamps to stream
    # captures:
    if "#t=" in entry["youtube"]:
        youtube_metadata = get_youtube_timestamps_title_description(entry)
    else:
        youtube_metadata = get_youtube_entry_title_description(entry)

    video_metadata = get_youtube_metadata(entry)

    description = youtube_metadata["description"]
    description = description.replace("<", "-")
    description = description.replace(">", "-")
    description = description.strip()

    title = youtube_metadata["title"]
    title = title.replace("<", "-")
    title = title.replace(">", "-")
    title = title.strip()

    return YoutubeInfo(
        title=title[:YOUTUBE_MAX_TITLE_LENGTH],
        description=description,
        tags=list(video_metadata["tags"]),
        category=video_metadata["category"],
    )


def reorder_positioned_section_entries(inout_entries: typing.List[Entry]):
    def _get_key(value):
        return value.get("position", 99999)
    inout_entries.sort(key=_get_key)


def get_clean_youtube_id(entry: Entry) -> typing.Optional[str]:
    """Clean timestamps references from a Youtube ID"""
    youtube_id = entry.get("youtube", None)
    if not youtube_id:
        return None
    cleaned = youtube_id.split("?", 1)[0]
    cleaned = cleaned.split("#", 1)[0]
    return cleaned


def get_clean_twitch_id(entry: Entry) -> typing.Optional[str]:
    """Clean timestamps references from a Twitch ID"""
    twitch_id = entry.get("twitch", None)
    if not twitch_id:
        return None
    # twitch-id#0h0m12s
    cleaned = twitch_id.split("?", 1)[0]
    return cleaned


def get_timed_twitch_id(entry: Entry) -> typing.Optional[str]:
    """Twitch IDs are timed as they are"""
    return entry.get("twitch")


def get_timed_youtube_id(entry: Entry) -> typing.Optional[str]:
    """Get youtube timestamps in seconds"""
    youtube_id = entry.get("youtube", None)
    if not youtube_id:
        return None
    if "=" not in youtube_id:
        return youtube_id
    clean_id = get_clean_youtube_id(entry)
    _, timestamp = youtube_id.split("=", 1)
    try:
        seconds = int(timestamp)
        return "%s#t=%d" % (clean_id, seconds)
    except ValueError:
        pass

    total_seconds = 0
    houred = timestamp.split("h", 1)
    if len(houred) == 2:
        total_seconds += int(houred[0]) * 3600
        timestamp = houred[1]
    minuted = timestamp.split("m", 1)
    if len(minuted) == 2:
        total_seconds += int(minuted[0]) * 60
        timestamp = minuted[1]
    seconded = timestamp.split("s", 1)
    if len(seconded) == 2:
        total_seconds += int(seconded[0])
    return "%s#t=%d" % (clean_id, total_seconds)
