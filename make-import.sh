#!/bin/bash

set -eu

source "$(dirname "$0")"/variables.inc.sh

$PYTHON "$SCRIPTDIR"/create-import-data.py --pms-vote-template="$PMS_ROOT"/"$PMS_PARTY"/compos/%s/vote/ --no-empty "$FILES_ROOT" "$@" < "$DATAFILE" > "$OUTFILE"
