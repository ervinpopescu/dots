#!/bin/bash

DOTS_FOLDER="${DOTS_FOLDER:-$HOME/www/src/mine/dots}"

if [ ! -d "$DOTS_FOLDER" ]; then
    echo "Error: Directory '$DOTS_FOLDER' does not exist." >&2
    exit 1
fi

cd "$DOTS_FOLDER" || exit 1

# Check for required commands
for cmd in git curl dots-dir-tree.sh pkglist-backup.sh qtilekeys.py; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: Required command '$cmd' is not installed or not in PATH." >&2
        exit 1
    fi
done

dots-dir-tree.sh "$DOTS_FOLDER"
pkglist-backup.sh "$DOTS_FOLDER"
printf '%s\n\n' "# Keybindings" > keybinds.md
qtilekeys.py md >> keybinds.md
sed -i.bak -e '/--------/a | |\n|**WINDOWS & GROUPS**|\n| |' keybinds.md
sed -i.bak -e '/Minimize all windows in all groups/a | |\n|**LAYOUTS**|\n| |' keybinds.md
sed -i.bak -e '/Grow down (bsp&col)/a | |\n| **LAYOUT MANAGING**  |\n| |' keybinds.md
sed -i.bak -e '/Shuffle down/a | |\n| **WINDOW MANAGING**  |\n| |' keybinds.md
sed -i.bak -e '/Kill window/a | |\n| **QTILE**            |\n| |' keybinds.md
sed -i.bak -e '/layout on all groups/a | |\n| **APPS** |\n| |' keybinds.md
sed -i.bak -e '/Open flameshot/a | |\n| **DE KEYS**  |\n| |' keybinds.md
sed -i.bak -e 's/||/\\|\\|/g' keybinds.md
rm keybinds.md.bak

# Only commit if there are changes
if [ -n "$(git -C "$DOTS_FOLDER" status --porcelain)" ]; then
    git -C "$DOTS_FOLDER" add .
    
    # Try to get a funny commit message, fallback to timestamp if it fails
    commit_msg=$(curl -sk https://whatthecommit.com/index.txt)
    if [ -z "$commit_msg" ]; then
        commit_msg="Update dotfiles: $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    
    git -C "$DOTS_FOLDER" commit -m "$commit_msg"
    git -C "$DOTS_FOLDER" push
else
    echo "No changes to commit."
fi
