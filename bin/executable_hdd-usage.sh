#!/bin/bash

# Check disk usage for the file system containing the current directory (or root)
# -h for human readable, -k for 1K blocks (portability)

if command -v df >/dev/null; then
    # Portable way to get usage of the partition containing /
    # output format of df -h: Filesystem Size Used Avail Capacity Mounted on
    # We want Capacity (usually 5th column, but sometimes lines wrap)
    
    # Try to use df -h and parse
    output=$(df -h "$HOME" | awk 'NR==2 {print $5, $3 "/" $2}')
    usage_percent=$(echo "$output" | awk '{print $1}')
    usage_ratio=$(echo "$output" | awk '{print $2}')
    
    # Remove % sign
    echo "$usage_ratio (${usage_percent%\%})"
else
    echo "df command not found"
    exit 1
fi
