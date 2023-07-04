#!/bin/python

import os
import subprocess

from libqtile.command.client import InteractiveCommandClient

from rofi import Rofi

c = InteractiveCommandClient()


def dunstify(string):
    subprocess.run(f"dunstify -a layout -u normal -r 323131 {string}".split())


groups = c.get_groups()
keys = list(groups.keys())
layouts: str = groups[keys[0]]["layouts"]

folder = "/usr/lib/python3.10/site-packages/libqtile/resources/layout-icons/"
icons = os.listdir(folder)
icons.sort()

options = [None] * len(layouts)

for icon in icons:
    for layout in layouts:
        if layout in icon:
            options[layouts.index(layout)] = f" {layout}" + f"\x00icon\x1f{folder}" + icon
# print(options)
r = Rofi(
    lines=len(layouts),
    rofi_args=[
        "-config",
        os.path.join(
            os.path.expanduser("~"),
            ".config",
            "rofi",
            "layouts.rasi",
        ),
        "show-icons",
    ],
)
print(r.rofi_args)
index, key = r.select(
    prompt="Select layout",
    options=options,
)

if key == 0:
    # dunstify(layouts[index])
    c.group.setlayout(layouts[index])
