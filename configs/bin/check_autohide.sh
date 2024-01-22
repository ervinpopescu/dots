#!/bin/bash
while true
do
    if ! pgrep autohide.py &>/dev/null
    then
        autohide.py &
    fi
    sleep 10
done