#!/bin/bash

# IFS=$'\n'
readarray -t macs < <(bluetoothctl devices | awk '{print $2}')
# readarray -t names < <(bluetoothctl devices | awk '{$1=$2=""; print $0}' | sed 's/^[ \t]*//')
num_devices=${#macs[@]}
for ((i = 0; i < num_devices; i++)); do
  is_connected="$(bluetoothctl info "${macs[$i]}" | grep Connected | awk '{print $2}')"
  if [[ "$is_connected" != "no" ]]; then
    battery="$(bluetoothctl info "${macs[$i]}" | grep Battery | sed 's/.*(\(.*\))/\1/')"
    printf "%s" "$battery"
  fi
done
