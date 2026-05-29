#!/bin/bash

if ! command -v pacman >/dev/null 2>&1; then
    echo "Error: 'pacman' not found. This script requires Arch Linux."
    exit 1
fi

table="$(LC_ALL=C pacman -Qi | awk '/^Name/{name=$3} /^Required By/{if($NF=="None") {required_by=0} else {required_by=NF-3}} /^Installed Size/{print $4$5, name, required_by""}' | sort -hr | column -N "Installed Size,Name,Required By" -J| jq '.table')"

printf '%s\n' "$table" | markdown_table.py
