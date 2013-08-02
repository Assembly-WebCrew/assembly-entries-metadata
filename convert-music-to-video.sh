#!/bin/bash

source "$(dirname "$0")"/variables.inc

CATEGORY="$1"

cd "$FILES_ROOT" || exit 1
test -d "$CATEGORY" || exit 1
test -f "$MUSIC_BACKGROUND" || exit 1

IDFILE=$(mktemp -u --suffix .wav)
function cleanup {
    rm "$IDFILE"
}
trap cleanup EXIT

for MUSIC_FILE in "$CATEGORY"/{*.wav,*.ogg,*.mp3}; do
    TARGET_FILE="$MUSIC_FILE".avi

    mplayer -ao pcm:file="$IDFILE" "$MUSIC_FILE"
    LENGTH=$(mplayer -ao null -vo null -frames 0 -identify -really-quiet "$IDFILE" | grep ID_LENGTH | cut -f 2 -d =)

    mencoder -fps 1/"$LENGTH" -ofps 30 -o "$TARGET_FILE" -ovc lavc -oac copy -audiofile "$IDFILE" mf://"$MUSIC_BACKGROUND"
done
