#!/bin/sh

if command -v paplay >/dev/null 2>&1; then
    paplay /usr/share/sounds/freedesktop/stereo/message.oga
elif command -v afplay >/dev/null 2>&1; then
    # macOS default sound
    afplay /System/Library/Sounds/Glass.aiff
fi
