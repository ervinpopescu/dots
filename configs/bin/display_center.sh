#!/bin/bash

columns="$(tput cols)"
while IFS= read -r line; do
    printf "%*s\n" $(( (${#line} + columns) / 2)) "$line"
done < "$1"