#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

SECTION="$1"
PMS_EXPORT_DATA=$FILES_ROOT/$SECTION/pms-export.xml

OUTPUT_TEMPFILE="$DATAFILE"-merged.txt

"${PYTHON[@]}" "$SCRIPTDIR"/pms-parse-export-data.py "$DATAFILE" "$PMS_EXPORT_DATA" "$SECTION" > "$OUTPUT_TEMPFILE"
cat "$OUTPUT_TEMPFILE" > "$DATAFILE"
