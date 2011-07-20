# -*- coding: utf-8 -*-

import re

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
    entries = {}


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
                assert not normalized_section in result.entries
                section = {
                    'key': normalized_section,
                    'name': section_name,
                    }
                result.sections.append(section)
                result.entries[normalized_section] = []
            elif data_type == ":description":
                # Descriptions can only be under section.
                assert section is not None
                # Only one description per section is allowed.
                assert 'description' not in section
                section['description'] = value
            else:
                raise RuntimeError, "Unknown type %s." % data_type
            continue

        assert year is not None
        assert section is not None

        data_dict = dict((str(x.split(":", 1)[0]), x.split(":", 1)[1]) for x in line.split("|"))

        position = int(data_dict.get('position', u'0'))
        if position != 0:
            data_dict['position'] = position
        else:
            del data_dict['position']

        result.entries[normalized_section].append(data_dict)

    return result

