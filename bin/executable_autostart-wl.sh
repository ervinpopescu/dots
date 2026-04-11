#!/bin/sh

## "daemons"
gnome-keyring-daemon --start &
/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
battery-notification.py &
dunst &
# /usr/lib/kdeconnectd &

## wallpaper
run_wall_wl.sh rand all &

## various apps
# $HOME/.config/conky/start_qtile.sh -n &
yes | rmshit.py &
# firefox &
# alacritty &

## systray
# nm-applet &
nm-tray &
pa-applet --disable-key-grabbing --disable-notifications &
blueman-tray &
# blueman-applet &
# flameshot &
# waybar &
# kdeconnect-indicator &
