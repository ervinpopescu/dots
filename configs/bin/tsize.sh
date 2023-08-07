#!/bin/sh

tput cols lines | tr "\n" " " | sed 's/ /x/'
