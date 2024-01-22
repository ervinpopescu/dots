#!/bin/bash

## load X11 defaults
xrdb -merge ~/.config/X11/Xresources &
autorandr --load default
xclickroot -l 'nwgbar -b 1d1d2d -o 0.4' &

## "daemons"
battery-notification.py &
# search_phone.sh &
/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
/usr/lib/kdeconnectd &
# activate-linux -id -s 1.5 -f 'CodeNewRoman Nerd Font Mono Bold' &
alttab -w 1 -d 2 -i 120x80 -t 120x80 -bg "#1e1d2d" -fg "#d9e0ee" -frame "#ddb6f2" -bw 5 -inact "#1e1d2d" -bc "#000000" -bw 0 -theme hicolor &
dunst &
# setsid -f restart_qtile_on_config_change.sh
gnome-keyring-daemon --start &
libinput-gestures-setup start &
setxkbmap -option "terminate:ctrl_alt_bksp" &
xmousepasteblock &
# xsettingsd &

## wallpaper
# change_wallpaper.sh rand &
change_wallpaper.sh /home/ervin/Pictures/wallpapers/rand/windowsy.png &

## theme
# change_theme.py &

## lockscreen
xset s 1800 &
xss-lock -- betterlockscreen -l dimblur &

## various apps
yes | rmshit.py &
dex /usr/share/applications/plank.desktop &
# /home/ervin/.config/conky/start_qtile.sh -n &
# firefox &
# codium &
# alacritty &

## systray
mictray &
nm-applet &
blueman-applet &
flameshot &
battery-profile.py &
power-profile.py &
pa-applet --disable-key-grabbing --disable-notifications &
kdeconnect-indicator &

## compositor
picom --config /home/ervin/.config/picom.conf &
# ~/.screenlayout/work.sh &

pids=$(jobs -p)
printf '%s\n' "$pids" > /tmp/autostart_pids
