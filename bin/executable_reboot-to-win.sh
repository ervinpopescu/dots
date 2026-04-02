#!/bin/sh

number=$(efibootmgr | grep Windows | sed 's/Boot//;s/\*//' | cut -d" " -f1)
sudo efibootmgr -n "$number"
systemctl reboot
