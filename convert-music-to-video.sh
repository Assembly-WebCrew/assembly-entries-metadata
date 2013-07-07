#!/bin/sh

set -e
set -u

MUSIC_FILE="$1"
IMAGE_FILE="$2"
TARGET_FILE="$3"

test -s "$MUSIC_FILE" || exit 1
test -s "$IMAGE_FILE" || exit 1
test -s "$TARGET_FILE" && exit 1

IDFILE=$(mktemp -u)
mplayer -ao pcm:file="$IDFILE".wav "$MUSIC_FILE"
LENGTH=$(mplayer -ao null -vo null -frames 0 -identify -really-quiet "$IDFILE".wav | grep ID_LENGTH | cut -f 2 -d =)
rm "$IDFILE".wav

mencoder -fps 1/"$LENGTH" -ofps 30 -o "$TARGET_FILE" -ovc lavc -oac copy -audiofile "$MUSIC_FILE" mf://"$IMAGE_FILE"
