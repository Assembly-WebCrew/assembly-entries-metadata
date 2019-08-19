#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

"${PYTHON[@]}" "$SCRIPTDIR"/create-tarball-export.py \
    -o "$OUTFILE" \
    --pms-vote-template="$PMS_ROOT"/"$PMS_PARTY"/compos/%s/vote/ \
    --no-empty \
    "$DATAFILE" \
    "$FILES_ROOT" \
    "$@"
