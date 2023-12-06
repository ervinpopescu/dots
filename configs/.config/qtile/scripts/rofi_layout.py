#!/bin/python

import inspect
import json
import os
import pathlib

import notify2
from libqtile.command.client import InteractiveCommandClient
from rofi import Rofi

notify2.init("rofi_layout")

c = InteractiveCommandClient()
with open(
    os.path.join((pathlib.Path(c.qtile_info()["config_path"]).parent), "json", "settings.json"),
    "r",
) as f:
    group_layouts = json.load(f)["group_layouts"]
print(group_layouts)

groups = c.get_groups()
keys = list(groups.keys())
layouts: str = groups[keys[0]]["layouts"]

folder = f"{pathlib.Path(inspect.getfile(InteractiveCommandClient)).parent.parent}/resources/layout-icons/"
icons = os.listdir(folder)
icons.sort()

options = [None] * len(layouts)

for icon in icons:
    for layout in layouts:
        if layout in icon:
            options[layouts.index(layout)] = f" {layout}" + f"\x00icon\x1f{folder}" + icon
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
index, key = r.select(
    prompt="Select layout",
    options=options,
)

if key == 0:
    notify2.Notification(layouts[index]).show()
    c.group.setlayout(layouts[index])
