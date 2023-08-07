#!/bin/python

import os
import sys
from time import sleep

from xdo import Xdo

sys.path.insert(0, os.path.expanduser("~/.config/qtile-x11/"))
from libqtile.command.client import InteractiveCommandClient
from modules.settings import bar_height, margin_size

c = InteractiveCommandClient()

while True:
    xdo = Xdo()
    xm = xdo.get_mouse_location().x
    ym = xdo.get_mouse_location().y
    bar = c.screen.bar["top"].info()
    size = bar["size"]
    if size == bar_height + margin_size:
        visible = True
    elif size == 0:
        visible = False
    if ym == 0 and xm == 0:
        x = 100
        y = 100
        c.hide_show_bar("top")
        xdo.move_mouse(x, y)
    sleep(0.05)
