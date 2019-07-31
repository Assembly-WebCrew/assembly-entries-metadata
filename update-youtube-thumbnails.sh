#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

mkdir -p "$FILES_ROOT"/youtube-thumbnails

"${PYTHON[@]}" "$SCRIPTDIR"/update-youtube-thumbnails.py "$FILES_ROOT"/youtube-thumbnails 160 90 < "$DATAFILE" &
"${PYTHON[@]}" "$SCRIPTDIR"/update-youtube-thumbnails.py "$FILES_ROOT"/youtube-thumbnails 200 112 < "$DATAFILE" &
"${PYTHON[@]}" "$SCRIPTDIR"/update-youtube-thumbnails.py "$FILES_ROOT"/youtube-thumbnails 240 135 < "$DATAFILE" &
"${PYTHON[@]}" "$SCRIPTDIR"/update-youtube-thumbnails.py "$FILES_ROOT"/youtube-thumbnails 320 180 < "$DATAFILE" &
"${PYTHON[@]}" "$SCRIPTDIR"/update-youtube-thumbnails.py "$FILES_ROOT"/youtube-thumbnails 480 270 < "$DATAFILE" &
"${PYTHON[@]}" "$SCRIPTDIR"/update-youtube-thumbnails.py "$FILES_ROOT"/youtube-thumbnails 640 360 < "$DATAFILE" &
wait
