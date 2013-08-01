#!/bin/sh

source "$(dirname "$0")"/variables.inc

$PYTHON "$SCRIPTDIR"/update-youtube-data.py "$DATAFILE" "$YOUTUBE_DEVELOPER_KEY" "$YOUTUBE_USER" "$YOUTUBE_EMAIL" "$YOUTUBE_PASSWORD"
