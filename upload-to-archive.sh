#!/bin/sh

source ./variables.inc

IMPORT_FILE="$1"
if test -z "$IMPORT_FILE"; then
    IMPORT_FILE="$OUTFILE"
fi

python "$SCRIPTDIR"/upload-to-archive.py "$WEB_UPLOAD_PAGE" "$WEB_UPLOAD_ACCOUNT" "$WEB_UPLOAD_PASSWORD" "$IMPORT_FILE"
