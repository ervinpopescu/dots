#!/bin/sh

history="$(grep -i "installed\|removed\|upgraded" /var/log/pacman.log | sed 's/\[ALPM\] //')"

printf '%s\n' "$history"
