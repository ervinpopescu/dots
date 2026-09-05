#!/usr/bin/env bash

# https://github.com/dastorm/volume-notification-dunst/blob/master/volume.sh
# https://gist.github.com/sebastiencs/5d7227f388d93374cebdf72e783fbd6a

function get_brightness {
  printf "%.0f" " $(($(brightnessctl g)*100/$(brightnessctl m)))"
}

function send_notification {
  icon="/usr/share/icons/Papirus-Dark/symbolic/status/display-brightness-symbolic.svg"
  # Send the notification
  notify-send -i "$icon" -a "brightness" -r 5555 -u low \
  -h int:value:"$brightness" "${brightness}%"
}

function update_external {
    local op=$1
    if command -v ddcutil >/dev/null 2>&1; then
        local cache_file="/tmp/ddcutil_buses"

        # If cache doesn't exist, create it synchronously (only slow the very first time)
        if [ ! -s "$cache_file" ]; then
            ddcutil detect --brief 2>/dev/null | grep "^Display" -A 1 | grep "I2C bus" | awk -F'-' '{print $2}' > "$cache_file"
        fi

        # If cache exists and is not empty, use it to update monitors in parallel
        if [ -s "$cache_file" ]; then
            while read -r bus; do
                if [ -n "$bus" ]; then
                    ddcutil setvcp 10 $op 10 --bus "$bus" >/dev/null 2>&1 &
                fi
            done < "$cache_file"
        fi
    fi
}

case $1 in
  up)
    # increase the backlight by 10%
    brightnessctl s 10%+
    update_external +
    brightness=$(get_brightness)
    send_notification
    ;;
  down)
    # decrease the backlight by 10%
    brightness=$(get_brightness)
    if [ "$brightness" -gt 12 ]
    then
      brightnessctl s 10%-
      update_external -
    fi
    brightness=$(get_brightness)
    send_notification
    ;;
esac
