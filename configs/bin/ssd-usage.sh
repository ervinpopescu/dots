#!/bin/bash

used="$(df -k /dev/nvme0n1p* | tr -s " " | cut -d" " -f3 | sed 1d | awk '{sum+=$1}END{print sum/1048576 "G";}')"
total="$(df -k /dev/nvme0n1p* | tr -s " " | cut -d" " -f2 | sed 1d | awk '{sum+=$1}END{print sum/1048576 "G";}')"

printf "%s" "$used / $total"