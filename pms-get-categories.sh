#!/bin/sh

source ./variables.inc

$PYTHON "$SCRIPTDIR"/get-categories.py "$PMS_ROOT" "$PMS_PARTY" "$PMS_LOGIN" "$PMS_PASSWORD"
