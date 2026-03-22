import os

import jsonpickle
from libqtile import hook
from libqtile.config import EzKey, Group, Key
from libqtile.lazy import lazy

from extras.mutablescratch import MutableScratch
from modules.groups.scratchpad import scratchpad
from modules.keys import keys
from modules.settings import config_path, settings


def go_to_group(name: str):
    def _inner(qtile):
        if len(qtile.screens) == 1:
            qtile.groups_map[name].toscreen(toggle=True)
            return
        else:
            screen = settings["groups"][name]["screen_affinity"]
            qtile.focus_screen(screen)
            qtile.groups_map[name].toscreen()

    return _inner


groups = []
keys_to_be_inserted = []
for i, name in enumerate(settings["groups"].keys(), 1):
    groups.append(
        Group(
            name=name,
            layout=settings["groups"][name]["layout"],
            label=settings["groups"][name]["label"],
            screen_affinity=settings["groups"][name]["screen_affinity"],
            layout_opts=None,
        )
    )
    keys_to_be_inserted.extend(
        [
            Key(
                [settings["keymaps"]["mod"]],
                str(i),
                lazy.function(go_to_group(name)),
                desc=f"Go to group `{name}`",
            ),
            Key(
                [settings["keymaps"]["mod"], "shift"],
                str(i),
                lazy.window.togroup(name),
                desc=f"Move window to group `{name}`",
            ),
        ]
    )
groups.append(scratchpad)

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
        EzKey(
            "M-C-<minus>",
            mutscr.remove(),
            desc="Remove window from MutableScratch",
        ),
    ]
)

pickled_keys = jsonpickle.encode(keys)
with open(os.path.join(config_path, "json", "keys.json"), "w") as f:
    f.write(pickled_keys)  # type: ignore

hook.subscribe.startup_complete(mutscr.qtile_startup)
