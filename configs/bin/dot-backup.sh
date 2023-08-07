#!/bin/bash

DOTS_FOLDER="/home/ervin/www/src/mine/dots"

cd "$DOTS_FOLDER" || exit 1

dots-dir-tree.sh "$DOTS_FOLDER"
pkglist-backup.sh "$DOTS_FOLDER"
printf '%s\n\n' "# Keybindings" > keybinds.md
qtilekeys.py md >> keybinds.md
sed -i -e '/--------/a | |\n|**WINDOWS & GROUPS**|\n| |' keybinds.md
sed -i -e '/Minimize all windows in all groups/a | |\n|**LAYOUTS**|\n| |' keybinds.md
sed -i -e '/Grow down (bsp&col)/a | |\n| **LAYOUT MANAGING**  |\n| |' keybinds.md
sed -i -e '/Shuffle down/a | |\n| **WINDOW MANAGING**  |\n| |' keybinds.md
sed -i -e '/Kill window/a | |\n| **QTILE**            |\n| |' keybinds.md
sed -i -e '/layout on all groups/a | |\n| **APPS** |\n| |' keybinds.md
sed -i -e '/Open flameshot/a | |\n| **DE KEYS**  |\n| |' keybinds.md
sed -i -e 's/||/\\|\\|/g' keybinds.md
git -C "$DOTS_FOLDER" add .
git -C "$DOTS_FOLDER" commit -m "$(curl -sk https://whatthecommit.com/index.txt)"
git -C "$DOTS_FOLDER" push
