#!/bin/sh

source "$(dirname "$0")"/variables.inc

$PYTHON "$SCRIPTDIR"/pms-get-categories.py "$PMS_ROOT" "$PMS_PARTY" "$PMS_LOGIN" "$PMS_PASSWORD"
