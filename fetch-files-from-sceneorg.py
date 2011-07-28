import asmmetadata
import os
import os.path
import subprocess
import sys

target_directory = sys.argv[1]
if not os.path.exists(target_directory):
    print "Target directory %s does not exist!" % target_directory
    sys.exit(1)

entry_data = asmmetadata.parse_file(sys.stdin)

for entry in entry_data.entries:
    if 'sceneorg' not in entry:
        continue
    sceneorg_path = entry['sceneorg']
    section_directory = entry['section']['key'].replace("-", "_")
    file_directory = asmmetadata.normalize_key("%s by %s" % (entry['title'], entry['author'])).replace("-", "_")
    download_directory = os.path.join(
        target_directory,
        section_directory,
        file_directory,
        )
    if not os.path.exists(download_directory):
        os.makedirs(download_directory)
    download_file = os.path.join(
        download_directory,
        os.path.basename(sceneorg_path)
        )
    download_url = "ftp://ftp.scene.org/pub%s" % sceneorg_path
    subprocess.call(['wget', '-O', download_file, download_url])
