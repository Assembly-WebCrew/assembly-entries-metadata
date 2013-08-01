#!/bin/sh

source "$(dirname "$0")"/variables.inc

$PYTHON "$SCRIPTDIR"/update-youtube-thumbnails.py "$FILES_ROOT"/youtube-thumbnails 160 90 < "$DATAFILE"
