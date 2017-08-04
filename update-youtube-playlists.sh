#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

exec "${PYTHON[@]}" "$SCRIPTDIR"/update-youtube-playlists.py "$DATAFILE" "${YOUTUBE_OPTIONS[@]}" "$@"
