#!/bin/bash

# @arg directory! <DIR>  Directory to search hardlinks in
# @arg target-directory! <DIR> Target directory to search hardlinks in

eval "$(argc --argc-eval "$0" "$@")"
# if [ "$1" == "-h" ] || [ "$1" == "" ]; then
#   printf "usage: find_hardlink [directory to search in] [target directory]"
#   exit 0
# fi

for i in $(exa -aghl -i "$2" | sed 1d | awk '{print $1}')
do
  printf '\033[0;31mfor the inode %s\033[0m\n' "$i";
  find "$1" -inum "$i" 2>/dev/null
done
