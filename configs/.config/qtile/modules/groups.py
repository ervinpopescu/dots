import os
import sys

import jsonpickle
from libqtile import hook, qtile
from libqtile.config import DropDown, EzKey, Group, Key, ScratchPad
from libqtile.core.manager import Qtile
from libqtile.lazy import lazy

from extras.mutablescratch import MutableScratch
from modules.keys import keys
from modules.path import config_path
from modules.settings import settings

qtile: Qtile
groups = [
    Group(
        name=settings["group_names"][i],
        layout=settings["group_layouts"][i],
        label=settings["group_labels"][i],
        layout_opts=None,
    )
    for i in range(len(settings["group_names"]))
]
screen_width = qtile.core.get_screen_info()[0][2]
screen_height = qtile.core.get_screen_info()[0][3]
scratchpad = ScratchPad(
    name="scratchpad",
    position=sys.maxsize,
    single=True,
    dropdowns=[
        DropDown(
            "term",
            settings["cmds"]["terminal"] + " --class=AlacrittyScratchpad",
            opacity=settings["dropdown_opacity"],
            width=1 - 2 * settings["margin_size"] / screen_width - 0.05,
            height=1 - 2 * settings["margin_size"] / screen_height - 0.05,
            x=settings["margin_size"] / screen_width + 0.025,
            y=settings["margin_size"] / screen_height + 0.025,
            on_focus_lost_hide=False,
        ),
        DropDown(
            "keys",
            "qtilekeys.py gtk",
            opacity=settings["dropdown_opacity"],
            width=1384 / screen_width,
            height=0.8,
            x=(1 - 1384 / screen_width) / 2,
            y=0.1,
            on_focus_lost_hide=False,
        ),
        DropDown(
            "htop",
            settings["cmds"]["htop"],
            opacity=settings["dropdown_opacity"],
            width=1 - 2 * settings["margin_size"] / screen_width - 0.05,
            height=1 - 2 * settings["margin_size"] / screen_height - 0.05,
            x=settings["margin_size"] / screen_width + 0.025,
            y=settings["margin_size"] / screen_height + 0.025,
            on_focus_lost_hide=False,
        ),
    ],
)
groups.append(scratchpad)

keys_to_be_inserted = []
for i, name in enumerate(settings["group_names"], 1):
    keys_to_be_inserted.extend(
        [
            Key(
                [settings["cmds"]["mod"]],
                str(i),
                lazy.group[name].toscreen(toggle=True),
                desc=f"Go to group {str(i)}",
            ),
            Key(
                [settings["cmds"]["mod"], "shift"],
                str(i),
                lazy.window.togroup(name),
                desc=f"Move window to group {str(i)}",
            ),
        ]
    )

keys[:0] = keys_to_be_inserted

mutscr = MutableScratch()
groups.append(Group(""))
keys.extend(
    [
        EzKey(
            "M-S-v",
            mutscr.add_current_window(),
            desc="Add current window to MutableScratch",
        ),
        EzKey("M-<minus>", mutscr.toggle(), desc="Toggle MutableScratch"),
        EzKey("M-C-<minus>", mutscr.remove(), desc="Remove window from MutableScratch"),
    ]
)
pickled_keys = jsonpickle.encode(keys)
with open(os.path.join(config_path, "json", "keys.json"), "w") as f:
    f.write(pickled_keys)

hook.subscribe.startup_complete(mutscr.qtile_startup)
