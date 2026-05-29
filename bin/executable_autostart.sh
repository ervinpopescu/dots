#!/bin/bash

set -u

# Helper to run a command if it exists
run_if_exists() {
    if command -v "$1" >/dev/null 2>&1; then
        "$@" &
    elif [ -x "$1" ]; then
        "$@" &
    fi
}

## load X11 defaults
if command -v xrdb >/dev/null; then
    xrdb -merge ~/.config/X11/Xresources &
fi

run_if_exists autorandr -c
run_if_exists run_wall.sh rand all

xset s 1800
xset +dpms
run_if_exists xclickroot -l 'nwgbar -b 1d1d2d -o 0.4'

## "daemons"
run_if_exists gnome-keyring-daemon --start --components=secrets

# Polkit agent (check common locations)
if [ -x "/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1" ]; then
    /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
fi

run_if_exists battery-notification.py
run_if_exists alttab
run_if_exists dunst
run_if_exists libinput-gestures-setup start
run_if_exists setxkbmap -option "terminate:ctrl_alt_bksp"
run_if_exists xmousepasteblock

## various apps
if command -v rmshit.py >/dev/null; then
    yes | rmshit.py &
fi
run_if_exists plank

## systray
run_if_exists mictray
run_if_exists nm-applet
run_if_exists blueman-applet
run_if_exists flameshot
run_if_exists systray_profile.py
run_if_exists pa-applet --disable-key-grabbing --disable-notifications

## compositor
run_if_exists picom --config "$HOME/.config/picom.conf"

# Save PIDs
pids=$(jobs -p)
printf '%s\n' "$pids" >/tmp/autostart_pids
