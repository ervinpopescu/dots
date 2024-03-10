#!/bin/bash

local_running="$(qtile cmd-obj -o cmd -f qtile_info | zsh -c 'qtile_to_json' | jq -r '.version' | sed 's/.*git\.//')"
local_installed="$(qtile --version | sed -r 's/.*git\.//')"
git="$(git -C /home/ervin/src/mine/qtile rev-parse --short master)"
if [[ "$git" != "$local_installed" ]]; then
	echo Please upgrade qtile
	exit 0
else
	if [[ "$local_installed" != "$local_running" ]]; then
		echo Please restart qtile
		exit 0
	else
		echo No need to upgrade
	fi
fi
