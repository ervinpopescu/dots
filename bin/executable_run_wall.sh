#!/bin/bash

pids=($(pgrep wallpaper.sh | sort -r))
n_pids=${#pids[@]}
for i in $(seq 0 $((n_pids - 1))); do
	kill -9 "${pids[$i]}"
done

wallpaper.sh "$@" &
