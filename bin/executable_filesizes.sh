#!/bin/bash

path="${1:-.}"

if [ ! -d "$path" ]; then
    echo "Error: Directory '$path' not found."
    exit 1
fi

# Use -d 1 (with space) for BSD/macOS compatibility. 
# Linux (GNU du) also supports -d, though --max-depth is standard.
# sort -h is standard in modern sort (GNU and BSD).

if du -h -d 1 "$path" >/dev/null 2>&1; then
    du -h -d 1 "$path" 2>/dev/null | sort -h
else
    # Fallback if -d is not supported (e.g. strict POSIX or old GNU)
    # uses --max-depth=1 for GNU
    du -h --max-depth=1 "$path" 2>/dev/null | sort -h
fi