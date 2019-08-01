#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

test -f "$MUSIC_BACKGROUND" || exit 1

TARGET_FILE=$MUSIC_BACKGROUND.mp4
# 20 minutes
MAX_FRAMES=12000

"${FFMPEG[@]}" -loop 1 -r 10 \
    -i "$MUSIC_BACKGROUND" \
    -frames "$MAX_FRAMES" \
    -c:v libx264 -r 10 -crf 0 -preset veryfast -shortest \
    -y "$TARGET_FILE"
