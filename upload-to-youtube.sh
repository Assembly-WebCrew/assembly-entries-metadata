#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

DATAFILE="${1:-$DATAFILE}"
DATAFILE_TMP="$(basename "$DATAFILE" .txt)-$(date +%Y%m%d%H%M%S).txt"

"${PYTHON[@]}" lib/upload-to-youtube-video.py "${YOUTUBE_OPTIONS[@]}" \
    --media-vod-directory="$FILES_MAO" "$FILES_ROOT" < "$DATAFILE" > "$DATAFILE_TMP"
cat "$DATAFILE_TMP" > "$DATAFILE"
