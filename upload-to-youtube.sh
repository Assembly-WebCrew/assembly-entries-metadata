#!/bin/sh

set -e
set -u

. ./variables.inc

DATAFILE="${1:-$DATAFILE}"
DATAFILE_TMP="$(basename "$DATAFILE" .txt)-$(date +%Y%m%d%H%M%S).txt"

"$PYTHON" lib/upload-to-youtube-video.py $YOUTUBE_UPLOAD_OPTIONS --media-vod-directory="$FILES_MAO" "$YOUTUBE_EMAIL" "$YOUTUBE_PASSWORD" "$FILES_ROOT" < "$DATAFILE" > "$DATAFILE_TMP" && \
    cat "$DATAFILE_TMP" > "$DATAFILE"
