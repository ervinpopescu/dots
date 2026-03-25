#!/bin/bash

export DW_BIN="/home/ervin/.local/share/dw/bin/dw"
DW_DIR="$HOME/dw-playground/"

[ -d "$DW_DIR" ] || mkdir "$DW_DIR"
cd "$DW_DIR" || exit 1

run-dw(){
  "$DW_BIN" -i payload payload.json "$(cat ./script.dwl)"
}
export -f run-dw

alacritty -e lvim ./script.dwl &
alacritty -e lvim ./payload.json &
alacritty -e watch -c -n 1 -t "bash -c run-dw"

# sleep 1
# xdotool key super+shift+Up
sleep 1
xdotool key super+shift+Down
