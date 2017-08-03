#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

"${PYTHON[@]}" "$SCRIPTDIR"/pms-get-categories.py \
    "$PMS_ROOT" "$PMS_PARTY" "$PMS_LOGIN" "$PMS_PASSWORD"
