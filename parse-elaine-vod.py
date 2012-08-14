import argparse
import asmmetadata
import os
import re
import shutil
import tempfile
import urllib2
import xml.dom.minidom

parser = argparse.ArgumentParser()
parser.add_argument("asmdatafile", type=argparse.FileType("r+b"))
parser.add_argument("elainexml")
args = parser.parse_args()

elaineFilePath = args.elainexml
if os.path.exists(elaineFilePath):
    elaineFilePath = "file://%s" % elaineFilePath

elainexml = urllib2.urlopen(elaineFilePath)

doc = xml.dom.minidom.parse(elainexml)
metadata_filename = args.asmdatafile.name
event_data = asmmetadata.parse_file(args.asmdatafile)
args.asmdatafile.close()

items = doc.getElementsByTagName("item")

def get_languaged_tag(item, tagname):
    nodes = item.getElementsByTagName(tagname)
    values = {}
    for node in nodes:
        value = None
        if node.firstChild is not None:
            value = node.firstChild.nodeValue
        language = node.getAttribute("xml:lang")
        values[language] = value
    return values

def get_entry(guid, section):
    for entry in section['entries']:
        if entry.get("guid") == guid:
            return entry
    return None

current_year = event_data.year
section_seminars = event_data.createSection("Seminars")
section_assemblytv = event_data.createSection("AssemblyTV")

for item in items:
    titles = get_languaged_tag(item, "title")
    title = titles.get('en', titles.get('fi', 'UNKNOWN TITLE'))
    descriptions = get_languaged_tag(item, "description")
    guid = item.getElementsByTagName("guid")[0].firstChild.nodeValue

    highestMedia = None
    mediaNodes = item.getElementsByTagName("media:group")[0]
    highestRate = 0
    highestType = None
    for mediaNode in mediaNodes.getElementsByTagName("media:content"):
        if mediaNode.getAttribute("url") == "":
            continue
        mediaType = mediaNode.getAttribute("type")
        size = int(mediaNode.getAttribute("fileSize"))
        bitrate = int(mediaNode.getAttribute("bitrate"))
        url = mediaNode.getAttribute("url")
        if bitrate > highestRate:
            highestRate = bitrate
            highestMedia = (url, mediaType, bitrate, size, title, guid)
            highestType = mediaType
        if bitrate == highestRate and highestType == "video/avi" and mediaType == "video/mp4":
            highestMedia = (url, mediaType, bitrate, size, title, guid)
            highestType = mediaType

    for categoryNode in item.getElementsByTagName("category"):
        if highestMedia is None:
            continue
        category = categoryNode.firstChild.nodeValue
        url, mediaType, bitrate, size, title, guid = highestMedia
        url = url.replace("http://media.assembly.org", "")
        guid = guid.replace("http://elaine.assembly.org/programs/", "")
        if re.match(r"\d\d\d\d AssemblyTV", category):
            year, _ = category.split(" ")
            year = int(year)
            if year != event_data.year:
                continue

            entry = get_entry(guid, section_assemblytv)
            if entry is None:
                entry_data = {
                    'author': "AssemblyTV",
                    }
                event_data.addEntry(section_assemblytv, entry_data)
            else:
                entry_data = entry
            entry_data['title'] = title
            entry_data['media'] = url
            entry_data['guid'] =  guid
            description = descriptions.get('en') or ""
            entry_data['description'] = description.strip() or None
        elif re.match(r"\d\d\d\d Seminars", category):
            year, _ = category.split(" ")
            year = int(year)
            if year != event_data.year:
                continue

            entry = get_entry(guid, section_seminars)
            if entry is None:
                entry_data = {
                    'author': "AssemblyTV seminars",
                    }
                event_data.addEntry(section_seminars, entry_data)
            else:
                entry_data = entry
            title = title.replace("ARTtech seminars - ", "")
            entry_data['title'] = title
            entry_data['media'] = url
            entry_data['guid'] =  guid

temporary_output = tempfile.NamedTemporaryFile(delete=False)
asmmetadata.print_metadata(temporary_output, event_data)
temporary_output.close()
shutil.copy(temporary_output.name, metadata_filename)

