#!/bin/sh

. ./variables.inc

python "$SCRIPTDIR"/get-categories.py "$PMS_ROOT" "$PMS_PARTY" "$PMS_LOGIN" "$PMS_PASSWORD"
