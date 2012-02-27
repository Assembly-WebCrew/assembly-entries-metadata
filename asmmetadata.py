# -*- coding: utf-8 -*-

import cgi
import hashlib
import re

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
        tags.extend(["assembly", str(year), "asm%d" % (year % 100), "Assembly %d" % year])
    elif 'winter' in section_name.lower():
        tags.extend(["assembly", str(year), "asm%d" % (year % 100), "asmw%d" % (year % 100), "Assembly Winter %d" % year])
    else:
        tags.extend(["assembly", str(year), "asm%d" % (year % 100), "asms%d" % (year % 100), "Assembly Summer %d" % year])
    if year == 2000:
        tags.append("asm2k")
    return tags

def get_long_section_name(section_name):
    if "winter" in section_name.lower():
        return u"AssemblyTV"
    elif "assemblytv" in section_name.lower():
        return u"AssemblyTV"
    elif "seminars" in section_name.lower():
        return u"Seminars"
    else:
        return u"%s competition" % section_name

def normalize_key(value):
    normalized = value.strip().lower()
    normalized = normalized.replace(u"ä", u"a")
    normalized = normalized.replace(u"ö", u"o")
    normalized = normalized.replace(u"å", u"a")
    normalized = re.sub("[^a-z0-9]", "-", normalized)
    normalized = re.sub("-{2,}", "-", normalized)
    normalized = normalized.strip("-")
    return normalized

class EntryYear(object):
    year = None
    sections = []
    entries = []


def parse_file(file_handle):
    result = EntryYear()

    year = None
    section = None
    normalized_section = None

    for line in file_handle:
        line = unicode(line.strip(), "utf-8")
        if line == "":
            continue
        if line[0] == "#":
            continue
        if line[0] == ":":
            data_type, value = line.split(" ", 1)
            if data_type == ":year":
                assert result.year is None
                year = int(value)
                result.year = year
            elif data_type == ":section":
                # Sections must have year.
                assert year is not None
                section_name = value
                normalized_section = normalize_key(section_name)
                assert not normalized_section in [section['key'] for section in result.sections]
                section = {
                    'key': normalized_section,
                    'name': section_name,
                    'year': year,
                    'entries': [],
                    }
                result.sections.append(section)
            elif data_type == ":description":
                # Descriptions can only be under section.
                assert section is not None
                # Only one description per section is allowed.
                assert 'description' not in section
                clean_value = value.strip()
                if len(clean_value):
                    section['description'] = clean_value
            elif data_type == ":youtube-playlist":
                assert section is not None
                assert 'youtube-playlist' not in section
                clean_value = value.strip()
                section['youtube-playlist'] = clean_value
            elif data_type == ":pms-category":
                # Categories can only be under section.
                assert section is not None
                # Only one category per section is allowed.
                assert 'pms-category' not in section
                clean_value = value.strip()
                if len(clean_value):
                    section['pms-category'] = clean_value
            elif data_type == ":ongoing":
                clean_value = value.strip()
                if clean_value.lower() == "true":
                    section['ongoing'] = True
            elif data_type == ":public":
                clean_value = value.strip()
                if clean_value.lower() == "false":
                    section['public'] = False
            else:
                raise RuntimeError, "Unknown type %s." % data_type
            continue

        assert year is not None
        assert section is not None

        try:
            data_dict = dict((str(x.split(":", 1)[0]), x.split(":", 1)[1]) for x in line.split("|"))
        except:
            print line
            raise

        position = int(data_dict.get('position', u'0'))
        if position != 0:
            data_dict['position'] = position
        elif 'position' in data_dict:
            del data_dict['position']

        assert 'section' not in data_dict
        data_dict['section'] = section

        result.entries.append(data_dict)
        section['entries'].append(data_dict)

    return result


def print_metadata(outfile, year_entry_data):
    outfile.write(":year %d\n" % year_entry_data.year)
    for section in year_entry_data.sections:
        outfile.write("\n:section %s\n" % section['name'])
        if 'youtube-playlist' in section:
            outfile.write(":youtube-playlist %s\n" % section['youtube-playlist'].encode("utf-8"))
        if 'pms-category' in section:
            outfile.write(":pms-category %s\n" % section['pms-category'])
        if 'description' in section:
            outfile.write(":description %s\n" % section['description'].encode("utf-8"))
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

        outfile.write("\n")

        for entry in section['entries']:
            del entry['section']
            parts = sorted(u"%s:%s" % (key, value) for key, value in entry.items())
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
    if 'webfile' in entry or 'image-file' in entry:
        filename = entry.get('webfile', None) or entry.get('image-file')
        baseprefix, _ = filename.split(".")
        if filename.endswith(".png") or filename.endswith(".jpeg") or filename.endswith(".gif"):
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
