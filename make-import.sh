#!/bin/sh

source ./variables.inc

$PYTHON "$SCRIPTDIR"/create-import-data.py --no-empty "$FILES_ROOT" < "$DATAFILE" > "$OUTFILE"
