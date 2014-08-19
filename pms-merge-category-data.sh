#!/bin/sh

source "$(dirname "$0")"/variables.inc.sh

COMPO_CATEGORY="$1"
shift
if test -z "$COMPO_CATEGORY"; then
    echo No compo category given.
    exit 1
fi

MERGE_TEMPFILE="$DATAFILE"-merged.txt

$PYTHON "$SCRIPTDIR"/merge-data-pms-archive.py "$@" "$DATAFILE" "$PMS_ROOT" "$PMS_PARTY" "$PMS_LOGIN" "$PMS_PASSWORD" "$COMPO_CATEGORY" > \
    "$MERGE_TEMPFILE" && cat "$MERGE_TEMPFILE" > "$DATAFILE"
