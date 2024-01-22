#!/bin/bash

if [[ "$(pamixer --get-mute)" == "false" ]]
then
	pamixer -m
	dunstify -a "changeVolume" -u low -I "$XDG_DATA_HOME/assets/volume-muted.svg" -r "991049" "Volume muted"
else
        pamixer -u
	dunstify -a "changeVolume" -u low -I "$XDG_DATA_HOME/assets/volume.svg" -r "991049" "Volume unmuted"
fi
