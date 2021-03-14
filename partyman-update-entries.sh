#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

export PARTYMAN_API_TOKEN
exec "${PYTHON[@]}" "$SCRIPTDIR"/partyman-update-entries.py "$DATAFILE"
