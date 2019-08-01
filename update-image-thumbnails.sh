#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

mkdir -p "$FILES_ROOT"/youtube-thumbnails

"${PYTHON[@]}" "$SCRIPTDIR"/update-image-thumbnails.py "$DATAFILE" "$FILES_ROOT" thumbnails/small 160
"${PYTHON[@]}" "$SCRIPTDIR"/update-image-thumbnails.py "$DATAFILE" "$FILES_ROOT" thumbnails/large 640 --no-height
