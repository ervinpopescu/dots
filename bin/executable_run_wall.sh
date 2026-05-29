#!/bin/bash

# Kill any existing wallpaper.sh instances
pkill -f "wallpaper.sh" || true

# Start new instance
wallpaper.sh "$@" &
