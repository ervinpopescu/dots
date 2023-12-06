#!/bin/bash

player_status() {
  if [[ "$(playerctl status)" == "Playing" ]]
  then
    printf '%s\n' ""
  else 
    printf '%s\n' "" 
  fi
}

play_pause_text() {
  cat << EOF 
$(player_status)
$(playerctl metadata title; playerctl metadata artist)
EOF
}

case "$1" in
  "next")
    playerctl next
    sleep 2
    if [[ "$(playerctl metadata | awk '{print $1}' | uniq)" != "spotify" ]];then
      dunstify\
        -a "mediaNotification" \
        -i "$(playerctl metadata | grep artUrl | awk '{$1="";$2=""}1' | sed '3d;s/^[ \t]*//')" \
        -u low \
        -r '263723' \
        "$(playerctl metadata title; playerctl metadata artist)"
      fi
    ;;
  "previous")
    playerctl previous
    sleep 2
    if [[ "$(playerctl metadata | awk '{print $1}' | uniq)" != "spotify" ]];then
      dunstify\
        -a "mediaNotification" \
        -i "$(playerctl metadata | grep artUrl | awk '{$1="";$2=""}1' | sed '3d;s/^[ \t]*//')" \
        -u low \
        -r '263723' \
        "$(playerctl metadata title; playerctl metadata artist)"
    fi
  ;;
  "play-pause")
    playerctl play-pause 
    dunstify\
      -a "mediaNotification" \
      -i "$(playerctl metadata | grep artUrl | awk '{$1="";$2=""}1' | sed '3d;s/^[ \t]*//')" \
      -u low \
      -r '263723' \
      "$(play_pause_text)"  
  ;;
  "play")
    playerctl play
    dunstify\
      -a "mediaNotification" \
      -i "$(playerctl metadata | grep artUrl | awk '{$1="";$2=""}1' | sed '3d;s/^[ \t]*//')" \
      -u low \
      -r '263723' \
      "$(play_pause_text)"  
  ;;
  "pause")
    playerctl pause 
    dunstify\
      -a "mediaNotification" \
      -i "$(playerctl metadata | grep artUrl | awk '{$1="";$2=""}1' | sed '3d;s/^[ \t]*//')" \
      -u low \
      -r '263723' \
      "$(play_pause_text)"  
  ;;
esac
