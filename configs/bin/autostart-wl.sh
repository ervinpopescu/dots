#!/bin/sh

## "daemons"
gnome-keyring-daemon --start &
/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
/home/ervin/bin/battery-notification.sh &
dunst &
# /usr/lib/kdeconnectd &

## wallpaper
swaybg -i "$(xdg-user-dir PICTURES)"/wallpapers/rand/valley.png &

## various apps
# /home/ervin/.config/conky/start_qtile.sh -n &
yes | /home/ervin/bin/rmshit.py &
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

## compositor
picom &
