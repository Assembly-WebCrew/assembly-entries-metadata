#!/bin/sh

source "$(dirname "$0")"/variables.inc.sh

$PYTHON "$SCRIPTDIR"/parse-elaine-vod.py "$DATAFILE" "$ELAINE_VODS"
