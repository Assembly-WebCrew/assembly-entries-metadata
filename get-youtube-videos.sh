#!/bin/sh

PLAYLIST=PLJO4AtxKJiFONi7-VJ-Kkb1c3oLMENbif
yt-dlp -j $PLAYLIST | jq -r '"author:AssemblyTV|title:" + .title + "|youtube:" + .id' | tee list
