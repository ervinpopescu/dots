#!/bin/sh
# vim: ft=sh:ts=4:sw=4:et:ai:cin

cd "$(dirname "$0")" || exit
killall conky 2>/dev/null
if [ "$1" = "-n" ]; then
    pause_flag=""
else
    pause_flag="--pause=5"
    echo "Conky waiting 5 seconds to start..."
fi
conky --daemonize --quiet "$pause_flag" --config=./conky_qtile.conf