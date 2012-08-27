# -*- coding: utf-8 -*-

import argparse
import asmmetadata
import Levenshtein
import re
import tidy
import util
from xml.dom.minidom import parseString

parser = argparse.ArgumentParser()
parser.add_argument("asmdatafile", type=argparse.FileType("r+b"))
parser.add_argument("pouethtml", type=util.argparseTypeUrlOpenable)
args = parser.parse_args()

pouetHtml = args.pouethtml.read()

options = dict(output_xhtml=1, add_xml_decl=1, indent=1, tidy_mark=0)
pouetTidied = tidy.parseString(pouetHtml, **options)

pouetDom = parseString(str(pouetTidied))

links = pouetDom.getElementsByTagName("a")

products = []

for link in links:
    if "prod.php?which=" in link.getAttribute("href") and len(link.getElementsByTagName("img")) == 0:
        byNode = link.parentNode.nextSibling.nextSibling.nextSibling.nextSibling.firstChild
        name = re.sub("\s+", " ", link.childNodes[0].data).strip()
        if " by " in byNode.data:
            creator = re.sub("\s+", " ", byNode.nextSibling.firstChild.data).strip()
            name += " by " + creator
        pouetIdHref = link.getAttribute("href")
        pouetId = re.match(r"prod\.php\?which=(\d+)", pouetIdHref).group(1)
        assert len(pouetId)
        products.append((name.lower(), name, pouetId))

entry_data = asmmetadata.parse_file(args.asmdatafile)

for entry in entry_data.entries:
    normalizedEntryName = (entry['title'] + " by " + entry['author']).lower()

    distances = []
    for product in products:
        normalName, candidateName, candidateLink = product
        distances.append(Levenshtein.jaro(normalName, normalizedEntryName))

    maxMatch = max(distances)

    if maxMatch < 0.75:
        continue

    maxIndex = distances.index(maxMatch)

    normalized, candidateName, pouetId = products[maxIndex]
    del products[maxIndex]

    entry['pouet'] = pouetId

args.asmdatafile.seek(0)
args.asmdatafile.truncate()
asmmetadata.print_metadata(args.asmdatafile, entry_data)
