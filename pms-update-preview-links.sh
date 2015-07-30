#!/bin/bash

set -eu

source "$(dirname "$0")"/variables.inc.sh

COMPO_CATEGORY="$1"

if test -z "$COMPO_CATEGORY"; then
    echo No compo category given.
    exit 1
fi

$PYTHON "$SCRIPTDIR"/pms-update-preview-links.py "$DATAFILE" "$PMS_ROOT" "$PMS_PARTY" "$PMS_LOGIN" "$PMS_PASSWORD" "$COMPO_CATEGORY"
