#!/usr/bin/env bash

# https://github.com/dastorm/volume-notification-dunst/blob/master/volume.sh
# https://gist.github.com/sebastiencs/5d7227f388d93374cebdf72e783fbd6a

function get_brightness {
  printf "%.0f" " $(($(brightnessctl g)*100/$(brightnessctl m)))"
}

function send_notification {
  icon="/usr/share/icons/Papirus-Dark/symbolic/status/display-brightness-symbolic.svg"
  # Send the notification
  dunstify -I "$icon" -a "brightness" -r 5555 -u low \
  -h int:value:"$brightness" "${brightness}%"
}

case $1 in
  up)
    # increase the backlight by 10%
    brightnessctl s 10%+
    brightness=$(get_brightness)
    send_notification
    ;;
  down)
    # decrease the backlight by 10%
    brightness=$(get_brightness)
    if [ "$brightness" -gt 12 ]
    then
      brightnessctl s 10%-
    fi
    brightness=$(get_brightness)
    send_notification
    ;;
esac
