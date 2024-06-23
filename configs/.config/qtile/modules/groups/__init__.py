import os

import jsonpickle
from libqtile import hook
from libqtile.config import EzKey, Group, Key
from libqtile.lazy import lazy

from extras.mutablescratch import MutableScratch
from modules.keys import keys
from modules.settings import config_path, settings
from modules.groups.scratchpad import scratchpad

groups = [
    Group(
        name=settings["group_names"][i],
        layout=settings["group_layouts"][i],
        label=settings["group_labels"][i],
        layout_opts=None,
    )
    for i in range(len(settings["group_names"]))
]
groups.append(scratchpad)

keys_to_be_inserted = []
for i, name in enumerate(settings["group_names"], 1):
    keys_to_be_inserted.extend(
        [
            Key(
                [settings["keymaps"]["mod"]],
                str(i),
                lazy.group[name].toscreen(toggle=True),
                desc=f"Go to group {str(i)}",
            ),
            Key(
                [settings["keymaps"]["mod"], "shift"],
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
