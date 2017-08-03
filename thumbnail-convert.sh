#!/bin/bash

set -euo pipefail

source "$(dirname "$0")"/variables.inc.sh

cd "$FILES_ROOT" || exit 1
RESIZED_NAME=$(mktemp)
function cleanup()
{
    rm -f "$RESIZED_NAME"
}
trap cleanup EXIT

for D in "$@" ; do
    echo "$D"
    mkdir -p thumbnails/small/"$D"
    mkdir -p thumbnails/large/"$D"
    ls "$D"/*.png "$D"/*.jpeg "$D"/*.gif || :
    for SUF in png jpeg gif jpg PNG JPEG GIF JPG; do
        for I in "$D"/*."$SUF"; do
            echo "$I"
            test -f "$I" || continue
            BASE=$(basename "$I" ."$SUF")
            convert -resize 640x10000 "$I" thumbnails/large/"$D"/"$BASE".jpeg
            jpegoptim --strip-all thumbnails/large/"$D"/"$BASE".jpeg
            convert -resize 640x10000 "$I" thumbnails/large/"$D"/"$BASE".png
            zopflipng -m thumbnails/large/"$D"/"$BASE".png thumbnails/large/"$D"/"$BASE".png.z && mv thumbnails/large/"$D"/"$BASE".png.z thumbnails/large/"$D"/"$BASE".png

            convert "$I" -resize 160x5000 "$RESIZED_NAME"
            convert -gravity Center -crop 160x90+0+0 +repage "$RESIZED_NAME" thumbnails/small/"$D"/"$BASE".jpeg
            jpegoptim --strip-all thumbnails/small/"$D"/"$BASE".jpeg
            convert -gravity Center -crop 160x90+0+0 +repage "$RESIZED_NAME" thumbnails/small/"$D"/"$BASE".png
            zopflipng -m thumbnails/small/"$D"/"$BASE".png thumbnails/small/"$D"/"$BASE".png.z && mv thumbnails/small/"$D"/"$BASE".png.z thumbnails/small/"$D"/"$BASE".png
        done
    done
done
