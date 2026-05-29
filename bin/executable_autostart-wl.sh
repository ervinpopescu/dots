#!/bin/sh

# Helper to run a command if it exists
run_if_exists() {
    if command -v "$1" >/dev/null 2>&1; then
        "$@" &
    elif [ -x "$1" ]; then
        "$@" &
    fi
}

## "daemons"
run_if_exists gnome-keyring-daemon --start
if [ -x "/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1" ]; then
    /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
fi
run_if_exists "$HOME/bin/battery-notification.py"
run_if_exists dunst

## wallpaper
if command -v swaybg >/dev/null; then
    wallpaper_path="$(xdg-user-dir PICTURES)/wallpapers/rand/valley.png"
    if [ -f "$wallpaper_path" ]; then
        swaybg -i "$wallpaper_path" &
    fi
fi

## various apps
if command -v rmshit.py >/dev/null; then
    yes | "$HOME/bin/rmshit.py" &
fi

## systray
# nm-applet &
run_if_exists nm-tray
run_if_exists pa-applet --disable-key-grabbing --disable-notifications
run_if_exists blueman-tray

## compositor
run_if_exists picom
