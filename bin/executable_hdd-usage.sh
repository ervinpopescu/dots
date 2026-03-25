#!/bin/bash

[ -f /dev/sda ] || { printf "No HDD found"; exit 1; }
used="$(df -k /dev/sda* | tr -s " " | cut -d" " -f3 | sed 1d | awk '{sum+=$1}END{print sum/1048576 "G";}')"
total="$(df -k /dev/sda* | tr -s " " | cut -d" " -f2 | sed 1d | awk '{sum+=$1}END{print sum/1048576 "G";}')"

printf "%.2f" "$used / $total"
