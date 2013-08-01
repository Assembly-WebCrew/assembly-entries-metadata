#!/bin/sh

. "$(dirname "$0")"/variables.inc

$PYTHON "$SCRIPTDIR"/create-import-data.py --pms-vote-template=https://pms.paeae.fi/"$PMS_PARTY"/compos/%s/vote/ --no-empty "$FILES_ROOT" < "$DATAFILE" > "$OUTFILE"
