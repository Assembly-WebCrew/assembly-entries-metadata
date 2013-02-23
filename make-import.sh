#!/bin/sh

source ./variables.inc

python "$SCRIPTDIR"/create-import-data.py --no-empty "$FILES_ROOT" < "$DATAFILE" > "$OUTFILE"
