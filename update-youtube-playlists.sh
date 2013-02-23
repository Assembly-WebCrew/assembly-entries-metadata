#!/bin/sh

source ./variables.inc

python "$SCRIPTDIR"/update-youtube-playlists.py "$DATAFILE" "$YOUTUBE_DEVELOPER_KEY" "$YOUTUBE_USER" "$YOUTUBE_EMAIL" "$YOUTUBE_PASSWORD"
