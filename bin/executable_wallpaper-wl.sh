#!/bin/bash

folder="$(xdg-user-dir PICTURES)/wallpapers/rand"
wallpaper_folder_data="$XDG_DATA_HOME/wallpaper"
cache_until_now="$wallpaper_folder_data/tillnow"
# primary_display_wallpaper="$wallpaper_folder_data/output.png"

set_wall_and_lockscreen() {
  pkill swaybg
  if [[ "$2" == "all" ]]; then
    swaybg -o '*' -m fill -i "$1" &
  elif [[ "$2" != "" ]]; then
    swaybg -o "$2" -m fill -i "$1" &
  else
    echo "No displays specified" && exit 1
  fi
  ln -sf "$1" "$wallpaper_folder_data/lockscreen"
  notify-send -t 2000 "Wallpaper and lockscreen are set!"
}

case "$1" in
"rand")
  while true; do
    all=$(find "$folder" -maxdepth 1 \( ! -name .gitattributes \) -type f)
    n_all="$(wc -l <<<"$all")"
    shuffled="$(shuf -n "$n_all" <<<"$all")"
    readarray -t already <"$cache_until_now"
    if [ "$((n_all - 1))" -ne "$(wc -l <"$cache_until_now")" ]; then
      wallpaper="$(shuf -n 1 <<<"$shuffled")"
      while [[ "${already[*]}" =~ ${wallpaper} ]]; do
        wallpaper="$(shuf -n 1 <<<"$shuffled")"
      done
    else
      truncate -s 0 "$cache_until_now"
      wallpaper="$(shuf -n 1 <<<"$shuffled")"
    fi
    echo "$wallpaper" >>"$cache_until_now"
    set_wall_and_lockscreen "$wallpaper" "$2"
    sleep 7200
  done
  ;;
*)
  wallpaper="$1"
  {
    set_wall_and_lockscreen "$wallpaper" "$2"
    sleep 2
  } &>"$wallpaper_folder_data/log"
  ;;
esac
