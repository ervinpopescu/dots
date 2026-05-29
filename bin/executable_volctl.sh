#!/bin/bash

# Volume Control Script
# Usage: volctl.sh [+5%|-5%]

msgId="991049"
step="${1:1}" # Extract number (e.g., 5 from -5 or +5)
direction="${1:0:1}" # Extract sign (- or +)
icon="$HOME/.local/share/assets/volume.svg"

# Determine Volume Control Command
if command -v pamixer >/dev/null 2>&1; then
    # Linux / PulseAudio
    if [[ "$direction" == "-" ]]; then
        pamixer --allow-boost -d "$step" >/dev/null
    else
        pamixer --allow-boost -i "$step" >/dev/null
    fi
    volume="$(pamixer --get-volume-human)"
    
elif command -v osascript >/dev/null 2>&1; then
    # macOS
    current_vol=$(osascript -e 'output volume of (get volume settings)')
    if [[ "$direction" == "-" ]]; then
        new_vol=$((current_vol - step))
    else
        new_vol=$((current_vol + step))
    fi
    
    # Clamp between 0 and 100
    if [ "$new_vol" -gt 100 ]; then new_vol=100; fi
    if [ "$new_vol" -lt 0 ]; then new_vol=0; fi
    
    osascript -e "set volume output volume $new_vol"
    volume="${new_vol}%"
else
    echo "Error: No supported volume control tool found (pamixer or osascript)." >&2
    exit 1
fi

# Notification (Optional)
if command -v dunstify >/dev/null 2>&1; then
    # Only show notification if icon exists, otherwise fallback to generic or no icon? 
    # Actually dunstify works without icon, but let's check.
    icon_arg=""
    if [ -f "$icon" ]; then
        icon_arg="-I $icon"
    fi

    dunstify \
        -a "changeVolume" \
        -u low \
        $icon_arg \
        -r "$msgId" \
        -h int:value:"${volume%\%}" "${volume}"
fi
