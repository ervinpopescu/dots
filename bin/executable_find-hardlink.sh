#!/bin/bash
# shellcheck disable=SC2154
# @arg directory! Directory to search hardlinks in
# @arg target-directory+ <DIR> Target directory

eval "$(argc --argc-eval "$0" "$@")"
files="$(find "$argc_target_directory" -type f | sort)"
for file in $files; do
  for i in $(exa -aghl -i "$file" | sed 1d | awk '{print $1}'); do
    printf '\033[0mFor the file \033[0;33m%s\033[0m we have inode \033[0;33m%s\033[0m and the following hardlinks:\n' "$file" "$i"
    find "$argc_directory" -inum "$i" 2>/dev/null
    printf "\n"
  done
done
