#!/bin/sh

source "$(dirname "$0")"/variables.inc

cd "$FILES_ROOT" || exit 1

for D in "$@" ; do
    echo "$D"
    mkdir -p thumbnails/small/"$D"
    mkdir -p thumbnails/large/"$D"
    ls "$D"/*.png "$D"/*.jpeg "$D"/*.gif
    for SUF in png jpeg gif jpg PNG JPEG GIF JPG; do
        for I in "$D"/*."$SUF"; do
            echo "$I"
            test -f "$I" || continue
            BASE=$(basename "$I" ."$SUF")
            convert -resize 640x10000 "$I" thumbnails/large/"$D"/"$BASE".jpeg
            jpegoptim --strip-all thumbnails/large/"$D"/"$BASE".jpeg
            convert -resize 640x10000 "$I" thumbnails/large/"$D"/"$BASE".png
            optipng -o7 thumbnails/large/"$D"/"$BASE".png

            convert "$I" -resize 160x5000 resized.png
            convert -gravity Center -crop 160x90+0+0 +repage resized.png thumbnails/small/"$D"/"$BASE".jpeg
            jpegoptim --strip-all thumbnails/small/"$D"/"$BASE".jpeg
            convert -gravity Center -crop 160x90+0+0 +repage resized.png thumbnails/small/"$D"/"$BASE".png
            optipng -o7 thumbnails/small/"$D"/"$BASE".png
        done
    done
done
