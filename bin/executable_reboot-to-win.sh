#!/bin/bash

if [[ "$(uname -s)" == "Darwin" ]]; then
    echo "Error: This script relies on efibootmgr/systemctl which are Linux-specific."
    echo "To reboot macOS, use: sudo shutdown -r now"
    exit 1
fi

if ! command -v efibootmgr >/dev/null 2>&1 || ! command -v systemctl >/dev/null 2>&1; then
    echo "Error: efibootmgr or systemctl not found."
    exit 1
fi

number=$(efibootmgr | grep Windows | sed 's/Boot//;s/\*//' | cut -d" " -f1)
if [ -n "$number" ]; then
    sudo efibootmgr -n "$number"
    systemctl reboot
else
    echo "Error: Windows boot entry not found."
    exit 1
fi