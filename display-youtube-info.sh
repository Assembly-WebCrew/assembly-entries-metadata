#!/usr/bin/env bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

exec "${PYTHON[@]}" "$SCRIPTDIR"/display-youtube-info.py "$DATAFILE" "$@"
