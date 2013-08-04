#!/bin/sh

source "$(dirname "$0")"/variables.inc

$PYTHON "$SCRIPTDIR"/parse-elaine-vod.py "$DATAFILE" "$ELAINE_VODS"
