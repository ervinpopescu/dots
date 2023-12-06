#!/bin/bash

folder=~/Pictures/wallpapers/rand

case $1 in
  "rand")
    while true
    do
      random="$(find $folder -maxdepth 1 -type f|shuf -n 1)"
      nitrogen  --set-zoom-fill "$random" & for job in $(jobs -p);do wait "$job"; done
      betterlockscreen -u "$random" --fx dimblur & for job in $(jobs -p);do wait "$job"; done
      notify-send -t 2000 "Lockscreen is set!"
      # /home/ervin/bin/android-wallpaper.sh "$random" & for job in $(jobs -p);do wait "$job"; done && android_success=1
      # if [[ $android_success == 1 ]]
      #   then
      #     notify-send -t 2000 "Android wallpaper and lockscreen are set!"
      #   else
      #     notify-send -t 2000 "Error, couldn't set Android wallpapers!"
      #   fi
      sleep 7200
    done;;
  *)
    nitrogen --set-zoom-fill "$1"
    betterlockscreen -u "$1" --fx dimblur & for job in $(jobs -p);do wait "$job"; done
    # /home/ervin/bin/android-wallpaper.sh "$1"
esac
