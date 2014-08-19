#!/bin/sh

set -e
set -u

source "$(dirname "$0")"/variables.inc.sh

MERGE_TEMPFILE="$DATAFILE"-merged.txt

$PYTHON "$SCRIPTDIR"/merge-filenames-pms-media.py "$DATAFILE" "$ELAINE_VODS" "$ELAINE_PMS_VODLIST" > "$MERGE_TEMPFILE" && cat "$MERGE_TEMPFILE" > "$DATAFILE"
