#!/bin/bash

OIFS="$IFS"
IFS=$'\n'

file="$1"
not_wanted="$(cat /home/ervin/.local/share/bad-wallpapers.txt)"

for f in $not_wanted
do
  if [[ "$f" == "$file" ]]
  then
    exit 1
  fi
done

dest=/sdcard/Download/wall
converted="/tmp/wall_converted"

teriyaki.sh scan
convert "$1" -gravity Center -crop 1080x2160+0+0 "$converted"
teriyaki.sh push "$converted" "$dest" || exit 1
teriyaki.sh wallpaper || exit 1

IFS="$OIFS"
