#!/bin/bash

table="$(LC_ALL=C pacman -Qi | awk '/^Name/{name=$3} /^Required By/{if($NF=="None") {required_by=0} else {required_by=NF-3}} /^Installed Size/{print $4$5, name, required_by""}' | sort -hk 3 | column -N "Installed Size,Name,Required By" -J| jq '.table')"

printf '%s\n' "$table" | markdown_table.py
