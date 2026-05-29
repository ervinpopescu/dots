#!/bin/bash

if ! command -v pacman >/dev/null 2>&1; then
    echo "Error: pacman not found." >&2
    exit 1
fi

if ! command -v markdown_table.py >/dev/null 2>&1; then
    echo "Error: markdown_table.py not found in PATH." >&2
    exit 1
fi

# Generate table data using jq
# Requires: pacman, awk, sort, column, jq
table_json=$(LC_ALL=C pacman -Qi | awk '/^Name/{name=$3} /^Required By/{if($NF=="None") {required_by=0} else {required_by=NF-3}} /^Installed Size/{print $4$5, name, required_by""}' | sort -hr | column -N "Installed Size,Name,Required By" -J)

# Extract table array from JSON and pass to markdown_table.py
echo "$table_json" | jq '.table' | markdown_table.py
