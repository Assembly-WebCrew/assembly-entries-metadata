import argparse
import asmmetadata
import re
import shutil
import tempfile
import util
import xml.dom.minidom

parser = argparse.ArgumentParser()
parser.add_argument("asmdatafile", type=argparse.FileType("r+b"))
parser.add_argument("elainexml", type=util.argparseTypeUrlOpenable)
args = parser.parse_args()

doc = xml.dom.minidom.parse(args.elainexml)
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


def get_entry_by_pms_path(pms_path, event_data):
    for section in event_data.sections:
        for entry in section['entries']:
            entry_pms_path = entry.get('pms-id')
            if entry_pms_path == pms_path:
                return entry
    return None


def get_entry_by_guid(guid, section):
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
    description = descriptions.get('en', descriptions.get("fi"))
    if description:
        description = description.strip()
    guid = item.getElementsByTagName("guid")[0].firstChild.nodeValue
    guid = guid.replace("http://elaine.assembly.org/programs/", "")

    entry = None
    path_len = len(item.getElementsByTagName("pms_path"))
    pms_path = None
    pms_path_child = item.getElementsByTagName("pms_path")[0].firstChild
    if pms_path_child:
        pms_path = pms_path_child.nodeValue
    if pms_path:
        entry = get_entry_by_pms_path(pms_path, event_data)

    if entry:
        entry['guid'] = guid

    youtube = None
    youtube_child = item.getElementsByTagName("youtube")[0].firstChild
    if youtube_child:
        youtube = youtube_child.nodeValue
    if entry and youtube:
        entry['youtube'] = youtube

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
            highestMedia = (url, mediaType, bitrate, size)
            highestType = mediaType
        if (bitrate == highestRate and
            highestType == "video/avi" and
            mediaType == "video/mp4"):
            highestMedia = (url, mediaType, bitrate, size)
            highestType = mediaType

    for categoryNode in item.getElementsByTagName("category"):
        url = None
        if highestMedia is not None:
            url, mediaType, bitrate, size = highestMedia
            url = url.replace("http://media.assembly.org", "")
        category = categoryNode.firstChild.nodeValue
        if re.match(r"\d\d\d\d AssemblyTV", category):
            year, _ = category.split(" ")
            year = int(year)
            if year != event_data.year:
                continue

            entry = get_entry_by_guid(guid, section_assemblytv)
            if entry is None:
                entry_data = {
                    'author': "AssemblyTV",
                }
                event_data.addEntry(section_assemblytv, entry_data)
            else:
                entry_data = entry
            entry_data['title'] = title
            entry_data['media'] = url
            entry_data['guid'] = guid
            if youtube:
                entry_data['youtube'] = youtube
            entry_data['description'] = description
        elif re.match(r"\d\d\d\d Seminars", category):
            year, _ = category.split(" ")
            year = int(year)
            if year != event_data.year:
                continue

            entry = get_entry_by_guid(guid, section_seminars)
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
            entry_data['guid'] = guid
            entry_data['description'] = description
            if youtube:
                entry_data['youtube'] = youtube


temporary_output = tempfile.NamedTemporaryFile(delete=False)
asmmetadata.print_metadata(temporary_output, event_data)
temporary_output.close()
shutil.copy(temporary_output.name, metadata_filename)
