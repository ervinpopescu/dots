#!/bin/bash

# Ensure required command exists
if ! command -v libinput-gestures-setup >/dev/null 2>&1; then
    echo "Error: libinput-gestures-setup not found." >&2
    exit 1
fi

CONFIG_DIR="$HOME/.config"
TARGET_CONF="$CONFIG_DIR/libinput-gestures.conf"

# Determine which config to link
if [[ "$XDG_SESSION_DESKTOP" == "qtile" ]]; then
    SOURCE_CONF="$CONFIG_DIR/libinput-gestures-qtile.conf"
else
    # Default fallback (budgie or others)
    SOURCE_CONF="$CONFIG_DIR/libinput-gestures-budgie.conf"
fi

if [ -f "$SOURCE_CONF" ]; then
    echo "Linking $SOURCE_CONF to $TARGET_CONF"
    ln -sf "$SOURCE_CONF" "$TARGET_CONF"
    libinput-gestures-setup restart
else
    echo "Warning: Config file $SOURCE_CONF not found. Skipping setup." >&2
fi
