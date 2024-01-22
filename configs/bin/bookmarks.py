#!/bin/python

import os
import subprocess

import rofi

file = os.path.join(os.path.expanduser("~"), ".local", "share", "bookmarks")

with open(file, "r") as f:
    bookmarks = f.readlines()

r = rofi.Rofi(lines=len(bookmarks))
index, key = r.select("Select bookmark", bookmarks)
if key == 0:
    subprocess.Popen(
        ["xdotool", "type", bookmarks[index]],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
