#!/bin/sh

source ./variables.inc

$PYTHON "$SCRIPTDIR"/update-youtube-thumbnails.py "$FILES_ROOT"/youtube-thumbnails 160 90 < "$DATAFILE"
