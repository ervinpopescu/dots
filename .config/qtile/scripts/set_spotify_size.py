#!/bin/env python
from time import sleep

from libqtile.command.client import InteractiveCommandClient

sleep(5)
c = InteractiveCommandClient()
wins = c.windows()
for i in range(0, len(wins)):
    if "spotify" in wins[i]["wm_class"][0]:
        c.group["media"].layout.set_ratio(0.85)
