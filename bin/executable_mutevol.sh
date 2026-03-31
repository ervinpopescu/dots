#!/bin/bash

if [[ "$(pamixer --get-mute)" == "false" ]]
then
	pamixer -m
	notify-send -a "changeVolume" -u low -i "$XDG_DATA_HOME/assets/volume-muted.svg" -r "991049" "Volume muted"
else
        pamixer -u
	notify-send -a "changeVolume" -u low -i "$XDG_DATA_HOME/assets/volume.svg" -r "991049" "Volume unmuted"
fi
