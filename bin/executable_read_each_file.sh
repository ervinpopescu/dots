#!/bin/bash

RED='\033[0;31m'
NC='\033[0m'

for each in "$@"
do
  if [ ! -d "${each}" ]
  then
    printf "%b" "${NC}${RED}--------------------------\n${each}\n--------------------------${NC}\n\n"
    head -13 "$each"
  fi
done | less -r
