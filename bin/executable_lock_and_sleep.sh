#!/bin/bash

swaylock -F -i ~/.local/share/wallpaper/lockscreen -s fill --effect-blur 10x5 --indicator --clock --timestr %H:%M --datestr %Y-%m-%d &
systemctl -i suspend
