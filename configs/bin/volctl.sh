#!/bin/bash

msgId="991049"

if [[ "${1:0:1}" == "-" ]];then
  pamixer --allow-boost -d "${1:1:1}" >/dev/null
else
  pamixer --allow-boost -i "${1:1:1}" >/dev/null
fi

volume="$(pamixer --get-volume-human)"
dunstify\
    -a "changeVolume"\
    -u low\
    -I "$HOME/.local/share/assets/volume.svg"\
    -r "$msgId"\
    -h int:value:"$volume" "${volume}"

# alert.sh
