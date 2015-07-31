#!/bin/bash

set -eu

source "$(dirname "$0")"/variables.inc.sh

IMPORT_FILE="${1:-$OUTFILE}"

$PYTHON "$SCRIPTDIR"/upload-to-archive.py "$WEB_UPLOAD_PAGE" "$WEB_UPLOAD_ACCOUNT" "$WEB_UPLOAD_PASSWORD" "$IMPORT_FILE"
