#!/usr/bin/env bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

mkdir -p "$FILES_ROOT"/youtube-thumbnails

CALL_PARAMS=(
    "${PYTHON[@]}"
    "$SCRIPTDIR"/update-image-thumbnails.py
    "$DATAFILE"
    "$FILES_ROOT"
)
LQ_PARAMS=(--low-quality)
if [[ -f $DATAROOT/mmod_human_face_detector.dat ]]; then
    LQ_PARAMS+=(--face-detect-model "$DATAROOT"/mmod_human_face_detector.dat)
fi

"${CALL_PARAMS[@]}" "${LQ_PARAMS[@]}" thumbnails/small 160
"${CALL_PARAMS[@]}" thumbnails/large 640 --no-height
