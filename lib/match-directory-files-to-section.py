#!/usr/bin/env python

import argparse
import asmmetadata
import os
import pyjarowinkler.distance
import re
import sys


def normalize_remove_suffix(value):
    return re.sub(r"(.)\.[^.]+$", "\\1", value)


def normalize_remove_numeric_prefix(value):
    return re.sub(r"^\d\d[.\- _]", "", value)


def select_best_candidates(entry, filenames):
    entry_key = asmmetadata.get_entry_key(entry)
    match_values = []
    max_distance = 0.0
    for filename in filenames:
        file_key = normalize_remove_numeric_prefix(filename)
        file_key = normalize_remove_suffix(file_key)
        file_key = asmmetadata.normalize_key(file_key)
        distance = pyjarowinkler.distance.get_jaro_distance(
            entry_key, file_key)
        max_distance = max(distance, max_distance)
        match_values.append((filename, distance))
    if max_distance < 0.75:
        return []
    return [x[0] for x in filter(lambda x: x[1] == max_distance, match_values)]


def select_bestest_match(entry, best_matches):
    for best_match in best_matches:
        if best_match.endswith(".diz"):
            continue
        return best_match
    raise ValueError("No best match for %s" % entry["name"])


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile")
    parser.add_argument("attribute_name", metavar="attribute-name")
    parser.add_argument("value_prefix", metavar="value-prefix")
    parser.add_argument("directory")
    parser.add_argument("section", type=unicode)
    args = parser.parse_args(argv[1:])

    entry_data = asmmetadata.parse_file(open(args.datafile, "rb"))

    section = entry_data.getSection(args.section)

    for _, _, filenames in os.walk(args.directory):
        filenames = [x.decode("utf-8") for x in filenames]
        # Just get the filenames.
        break

    for entry in section["entries"]:
        best_matches = select_best_candidates(entry, filenames)
        not_used_matches = []
        if len(best_matches) == 0:
            sys.stderr.write("NO MATCH: %s\n" % entry["title"])
            continue
        elif len(best_matches) > 1:
            best_match = select_bestest_match(entry, best_matches)
        else:
            best_match, = best_matches
        not_used_matches = best_matches[:]
        not_used_matches.remove(best_match)
        print("%s -> %s" % (asmmetadata.get_entry_key(entry), best_match))
        if len(not_used_matches) > 0:
            print("  UNUSED: %s" % ", ".join(not_used_matches))
        entry[args.attribute_name] = "%s:%s%s" % (
            args.attribute_name, args.value_prefix, best_match)
        for match in best_matches:
            filenames.remove(match)
    if len(filenames) > 0:
        print("EXTRA: %s" % ", ".join(filenames))
    asmmetadata.print_metadata(open(args.datafile, "wb"), entry_data)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
