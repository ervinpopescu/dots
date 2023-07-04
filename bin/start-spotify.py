#!/bin/python

import subprocess

# from time import sleep
from libqtile.command.client import InteractiveCommandClient

c = InteractiveCommandClient()
current_group = c.group.info()["name"]

if current_group != "media":
    c.screen.toggle_group("media")
    # c.group["media"].layout.set_ratio(0.8)
# c.spawn("glava -r 'mod bars-left'")
# c.spawn("glava -r 'mod bars-right'")
subprocess.call("dex /usr/share/applications/spotify.desktop", shell=True)
    # c.group["media"].layout.set_ratio(0.8)
