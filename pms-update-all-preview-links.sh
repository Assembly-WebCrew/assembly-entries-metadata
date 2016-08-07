#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

CATEGORIES=$(./pms-get-categories.sh)

echo "$CATEGORIES" | while read -r category; do
    ./pms-update-preview-links.sh "$category" || :
done
