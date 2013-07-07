#!/bin/sh

. ./variables.inc

python "$SCRIPTDIR"/update-youtube-thumbnails.py "$FILES_ROOT"/youtube-thumbnails 160 90 < "$DATAFILE"
