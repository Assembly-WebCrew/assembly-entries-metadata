#!/bin/bash

set -eu

source "$(dirname "$0")"/variables.sh

if test -z "$1" || test -z "$2"; then
    echo "Usage: $0 photo-category gallery-base-url"
    exit 1
fi

# photos-winter or photos-summer
PHOTO_CATEGORY="$1"
GALLERY_BASE_URL="$2"
PHOTOS_ROOT="$FILES_ROOT"/"$PHOTOS_ROOT"

mkdir -p "$PHOTOS_ROOT"

python lib/grab-galleriafi.py "$PHOTOS_ROOT" "$GALLERY_BASE_URL" > /tmp/asmphotos.txt
python lib/grab-galleriafi.py --download "$PHOTOS_ROOT" "$GALLERY_BASE_URL" | sh
