import argparse
import asmmetadata
import os.path

def check_directory(directory):
    if not os.path.isdir(directory):
        raise RuntimeError("Directory %s does not exist." % directory)
    return directory

parser = argparse.ArgumentParser()
parser.add_argument("sceneorg_directory", type=check_directory)
parser.add_argument("datafile", type=argparse.FileType('rb'))
args = parser.parse_args()

metadata_file = args.datafile
entry_data = asmmetadata.parse_file(args.datafile)

def sceneorg_name_base(title, author):
    name = "%s by %s" % (title, author)
    

def sceneorgify_entries(sceneorg_directory, section):
    for entry in section.entries:
        

for section in entry_data.sections:
    if not 'sceneorg' in section:
        continue
