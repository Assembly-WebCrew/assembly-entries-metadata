#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

mkdir -p "$FILES_ROOT"/youtube-thumbnails

"${PYTHON[@]}" "$SCRIPTDIR"/update-youtube-thumbnails.py "$DATAFILE" "$FILES_ROOT"/youtube-thumbnails
