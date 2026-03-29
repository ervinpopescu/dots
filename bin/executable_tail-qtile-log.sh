#!/bin/bash

cols="$(tsize.sh | awk -Fx '{print $2}')"
tail -$cols ~/.local/share/qtile/qtile.log
