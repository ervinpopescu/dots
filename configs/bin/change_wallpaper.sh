#!/bin/bash

pkill -KILL change_wallpaper
pkill -KILL wallpaper
pkill -KILL sleep
/home/ervin/bin/wallpaper.sh "$1" &
