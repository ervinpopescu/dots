#!/bin/env bash

rofi -show power-menu \
     -modi "power-menu:$HOME/.local/bin/rofi-power-menu --choices=suspend/logout/reboot/shutdown --confirm=reboot/shutdown" \
     -config $HOME/.config/rofi/powermenu.rasi
