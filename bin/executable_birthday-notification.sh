#!/bin/bash

dunstify\
    -a "birthdayNotification"\
    -u normal\
    -r "635325"\
    "$(birthday -W 0 -f ~/.local/share/birthdays)"
