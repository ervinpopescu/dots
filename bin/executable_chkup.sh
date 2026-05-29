#!/bin/bash

if command -v checkupdates &> /dev/null; then
    # Arch Linux
    number=$(checkupdates | wc -l)
elif command -v brew &> /dev/null; then
    # macOS / Homebrew - Suppress stderr (auto-update messages)
    number=$(brew outdated --greedy 2>/dev/null | wc -l | tr -d '[:space:]')
else
    number="?"
fi

printf "%s" "$number"