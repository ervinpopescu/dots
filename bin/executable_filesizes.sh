#!/bin/bash

# @option -f <PATH> Path 
eval "$(argc --argc-eval "$0" "$@")"
du -ahd1 "$argc_path" 2>/dev/null | sort -h
