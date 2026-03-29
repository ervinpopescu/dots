#!/bin/bash

pkgs_size.sh |
  q -d, -H 'select name from -' |
  fzf \
    -m \
    --header 'Press CTRL-R to reload' \
    --preview 'pacman -Qil {}' \
    --layout=reverse \
    --bind 'ctrl-r:reload(pkgs_size.sh | q -d, -H "select name from -")' \
    --bind 'enter:execute(sudo pacman -Rns {})+clear-query+reload(pkgs_size.sh | q -d, -H "select name from -")' \
    --bind end:last \
    --bind home:first
