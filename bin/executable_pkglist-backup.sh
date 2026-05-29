#!/bin/bash

# Default to current directory if not provided
TARGET_DIR="${1:-./configs}"

# Create directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Check for yay (Arch Linux)
if command -v yay >/dev/null 2>&1; then
    echo "Exporting Arch packages to $TARGET_DIR/pkgs..."
    yay -Qqe > "$TARGET_DIR/pkgs"
# Check for brew (macOS)
elif command -v brew >/dev/null 2>&1; then
    echo "Exporting Brewfile to $TARGET_DIR/Brewfile..."
    brew bundle dump --file="$TARGET_DIR/Brewfile" --force
else
    echo "No supported package manager found (yay or brew)." >&2
    exit 1
fi
