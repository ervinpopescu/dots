#!/bin/bash

interface="$(route | awk '{print $NF}' | tail -1)"

awk '{ if (l1) {\
        printf("↓%.2fMB/s ↑%.2fMB/s" \
               , ($2 - l1) / 1024 / 1024, ($10 - l2) / 1024 / 1024)
    } else {\
        l1=$2; l2=$10;\
    }\
}' <(grep "$interface" /proc/net/dev) <(sleep 1; grep "$interface" /proc/net/dev)
