#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

exec "${PYTHON[@]}" "$SCRIPTDIR"/update-youtube-data.py "$DATAFILE" "$@"
