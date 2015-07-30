#!/bin/bash

set -eu

source "$(dirname "$0")"/variables.inc.sh

$PYTHON "$SCRIPTDIR"/update-youtube-thumbnails.py "$FILES_ROOT"/youtube-thumbnails 160 90 < "$DATAFILE"
