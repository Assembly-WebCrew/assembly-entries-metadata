#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

PMS_COMPO_DUMP="$1"

OUTPUT_TEMPFILE="$DATAFILE"-merged.txt

"${PYTHON[@]}" "$SCRIPTDIR"/pms-parse-dump-compo-places.py "$DATAFILE" "$PMS_COMPO_DUMP" > "$OUTPUT_TEMPFILE"
cat "$OUTPUT_TEMPFILE" > "$DATAFILE"
