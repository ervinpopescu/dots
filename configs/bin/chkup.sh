#!/bin/bash

number=$(checkupdates | wc -l)
printf "%s" "$number"