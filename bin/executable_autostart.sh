#!/bin/bash

## load X11 defaults
xrdb -merge ~/.config/X11/Xresources &
autorandr -c && run_wall.sh rand all &
xset s 1800
xset +dpms
xclickroot -l 'nwgbar -b 1d1d2d -o 0.4' &

## "daemons"
gnome-keyring-daemon --start --components=secrets &
/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
battery-notification.py &
alttab &
dunst &
libinput-gestures-setup start &
setxkbmap -option "terminate:ctrl_alt_bksp" &
xmousepasteblock &
# search_phone.sh &
# activate-linux -id -s 1.5 -f 'CodeNewRoman Nerd Font Mono Bold' &
# setsid -f restart_qtile_on_config_change.sh
# xsettingsd &

## theme
# change_theme.py &

## various apps
yes | rmshit.py &
plank &
# /home/ervin/.config/conky/start_qtile.sh -n &
# firefox &
# codium &
# alacritty &

## systray
mictray &
nm-applet &
blueman-applet &
flameshot &
systray_profile.py &
pa-applet --disable-key-grabbing --disable-notifications &

## compositor
picom --config /home/ervin/.config/picom.conf &>/dev/null &

pids=$(jobs -p)
printf '%s\n' "$pids" >/tmp/autostart_pids
