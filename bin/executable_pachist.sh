#!/bin/bash

PACMAN_LOG="/var/log/pacman.log"

if [ ! -f "$PACMAN_LOG" ]; then
    echo "Error: $PACMAN_LOG not found. Are you on Arch Linux?" >&2
    exit 1
fi

# Extract history: Installed, Removed, Upgraded
# Format: [ALPM] upgraded foobar (1.0 -> 1.1)
# We remove the [ALPM] prefix for cleaner output
grep -i "installed\|removed\|upgraded" "$PACMAN_LOG" | sed 's/\[ALPM\] //'
