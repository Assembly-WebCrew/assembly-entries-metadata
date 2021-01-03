#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asmmetadata
import argparse
import io
import os
import sys
import typing


def print_sections(entry_data: asmmetadata.EntryYear, stream: io.TextIOBase):
    for section in entry_data.sections:
        stream.write("%s %s\n" % (section["key"], section["name"]))

class Range:
    start: typing.Optional[int] = None
    end: typing.Optional[int] = None

    def __init__(self, *, start=None, end=None):
        self.start = start
        self.end = end

    def matches(self, index: int) -> bool:
        if self.start is None and self.end is None:
            return True
        if self.start is None:
            if index <= self.end:
                return True
            return False
        if self.end is None:
            if self.start <= index:
                return True
            return False
        return self.start <= index and index <= self.end

    def __repr__(self):
        return "Range<start=%r,end=%r>" % (self.start, self.end)

class Ranges:
    ranges: list[Range] = []

    def __init__(self, ranges):
        self.ranges = ranges

    def matches(self, index: int) -> bool:
        for match_range in self.ranges:
            if match_range.matches(index):
                return True
        return False

    def __repr__(self):
        return "Ranges<%r>" % self.ranges

def type_entry_range(value) -> Ranges:
    """

    >>> range_individual = type_entry_range("2")
    >>> range_individual.matches(1)
    False
    >>> range_individual.matches(2)
    True
    >>> range_individual.matches(3)
    False

    >>> range_multiple_commas = type_entry_range("2,4")
    >>> range_multiple_commas.matches(1)
    False
    >>> range_multiple_commas.matches(2)
    True
    >>> range_multiple_commas.matches(3)
    False
    >>> range_multiple_commas.matches(4)
    True
    >>> range_multiple_commas.matches(5)
    False

    >>> range_multiple_continuous = type_entry_range("2-4")
    >>> range_multiple_continuous.matches(1)
    False
    >>> range_multiple_continuous.matches(2)
    True
    >>> range_multiple_continuous.matches(3)
    True
    >>> range_multiple_continuous.matches(4)
    True
    >>> range_multiple_continuous.matches(5)
    False

    >>> range_mixed = type_entry_range("2,3-4")
    >>> range_mixed.matches(1)
    False
    >>> range_mixed.matches(2)
    True
    >>> range_mixed.matches(3)
    True
    >>> range_mixed.matches(4)
    True
    >>> range_mixed.matches(5)
    False

    >>> range_unlimited_before = type_entry_range("-2")
    >>> range_unlimited_before.matches(1)
    True
    >>> range_unlimited_before.matches(2)
    True
    >>> range_unlimited_before.matches(3)
    False

    >>> range_unlimited_after = type_entry_range("2-")
    >>> range_unlimited_after.matches(1)
    False
    >>> range_unlimited_after.matches(2)
    True
    >>> range_unlimited_after.matches(3)
    True
"""
    error = ValueError("Range %r is not in format 1,2,4-6" % value)
    if not value:
        raise error
    unspaced = value.replace(" ", "")
    split_commas = unspaced.split(",")
    ranges = []
    for split_comma_value in split_commas:
        split_dash = split_comma_value.split("-")
        # Single number
        if len(split_dash) == 1:
            start_end = int(split_dash[0])
            ranges.append(Range(start=start_end, end=start_end))
            continue
        if len(split_dash) != 2:
            raise error
        start = None
        end = None
        if split_dash[0]:
            start = int(split_dash[0])
        if split_dash[1]:
            end = int(split_dash[1])
        ranges.append(Range(start=start, end=end))
    return Ranges(ranges)


def print_section_entries(ranges: Ranges, section):
    print("%d %s" % (section["year"], section["name"]))
    for index, entry in enumerate(section["entries"]):
        if not entry.get("youtube"):
            continue
        youtube_info = asmmetadata.get_youtube_info_data(entry)
        print("########## %d" % index)
        print("https://studio.youtube.com/video/%s/edit" % entry["youtube"])
        print(youtube_info["title"])
        print()
        print(youtube_info["description"])

def main(argv) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--ranges", type=type_entry_range, default=Ranges([Range()]))
    parser.add_argument("--section")
    parser.add_argument("datafile")
    args = parser.parse_args(argv[1:])

    entry_data = asmmetadata.parse_file(open(args.datafile, "r"))

    if args.list:
        if not args.section:
            print_sections(entry_data, sys.stdout)
            return os.EX_OK
        section = entry_data.getSection(args.section)
        if not section:
            sys.stderr.write(
                "ERROR: section %r is not part of the known sections:\n" % args.section)
            print_sections(entry_data, sys.stderr)
            return os.EX_USAGE
        return os.EX_OK

    if not args.section:
        sys.stderr.write("ERROR: need to give one of following sections as --section:\n")
        print_sections(entry_data, sys.stderr)
        return os.EX_USAGE
    section = entry_data.getSection(args.section)
    if not section:
        sys.stderr.write(
            "ERROR: section %r is not part of the known sections:\n" % args.section)
        print_sections(entry_data, sys.stderr)
        return os.EX_USAGE

    print_section_entries(args.ranges, section)
    return os.EX_OK

if __name__ == "__main__":
    sys.exit(main(sys.argv))
