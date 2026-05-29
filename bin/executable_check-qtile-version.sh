#!/bin/bash

if ! command -v qtile >/dev/null 2>&1; then
    echo "qtile not installed"
    exit 1
fi

if ! command -v git >/dev/null 2>&1; then
    echo "git not installed"
    exit 1
fi

repo_dir="$HOME/src/mine/qtile"
if [ ! -d "$repo_dir" ]; then
    echo "Qtile repo not found at $repo_dir"
    exit 1
fi

# Try to get running version
if ! local_running_json=$(qtile cmd-obj -o cmd -f qtile_info 2>/dev/null); then
    echo "Qtile is not running or not responding."
    exit 1
fi

# Parse version (assuming jq is available, or use python/grep)
if command -v jq >/dev/null 2>&1; then
    local_running=$(echo "$local_running_json" | jq -r '.version' | sed 's/.*git\.//')
else
    # Fallback sed parsing
    local_running=$(echo "$local_running_json" | sed -E 's/.*"version": "([^"]+)".*/\1/' | sed 's/.*git\.//')
fi

local_installed="$(qtile --version | sed -r 's/.*git\.//')"
git_ver="$(git -C "$repo_dir" rev-parse --short master)"

if [[ "$git_ver" != "$local_installed" ]]; then
	echo "Please upgrade qtile ($local_installed -> $git_ver)"
	exit 0
else
	if [[ "$local_installed" != "$local_running" ]]; then
		echo "Please restart qtile ($local_running -> $local_installed)"
		exit 0
	else
		echo "No need to upgrade"
	fi
fi
