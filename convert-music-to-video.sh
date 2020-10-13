#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

CATEGORY="$1"

cd "$FILES_ROOT" || exit 1
test -d "$CATEGORY" || exit 1
# Execute music-background-to-long-video.sh if this file is
# missing.
test -f "$MUSIC_BACKGROUND".mp4 || exit 1

for MUSIC_FILE in "$CATEGORY"/{*.aac,*.wav,*.ogg,*.mp3,*.flac,*.aif,*.aiff}; do
    [[ -f "$MUSIC_FILE" ]] || continue
    TARGET_FILE="$MUSIC_FILE".mp4

    # "${FFMPEG[@]}" -loop 1 -r 10 \
    #     -i "$MUSIC_BACKGROUND" -i "$MUSIC_FILE" \
    #     -c:a aac -b:a 384k \
    #     -c:v libx264 -r 10 -crf 0 -preset ultrafast -shortest \
    #     -y "$TARGET_FILE"
    "${FFMPEG[@]}" \
        -i "$MUSIC_BACKGROUND".mp4 -i "$MUSIC_FILE" \
        -shortest \
        -c:a copy \
        -c:v copy \
        -y "$TARGET_FILE"
done
