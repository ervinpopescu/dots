#!/bin/bash

mem=$(free -h | grep Mem | tr -s " " | cut -d" " -f3 | grep Mi)

if [  -z "${mem}"  ]
then
  Mem=$( free -h | grep Mem | tr -s " " | cut -d" " -f3 | sed 's/Gi/ Gi/')
  printf '%s\n' "$Mem"
else
  Mem=$(free -h | grep Mem | tr -s " " | cut -d" " -f3 | sed 's/Mi/ Mi/')
  printf '%s\n' "$Mem"
fi
