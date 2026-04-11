import os

import jsonpickle  # type: ignore
from libqtile import hook
from libqtile.config import EzKey, Group, Key
from libqtile.lazy import lazy

from extras.mutablescratch import MutableScratch
from modules.keys import keys
from modules.settings import config_path, settings
from modules.groups.scratchpad import scratchpad

groups = [
    Group(
        name=settings.groups[i].name,
        layout=settings.groups[i].layout,
        label=settings.groups[i].label,
        screen_affinity=settings.groups[i].screen_affinity,
        layout_opts=None,
    )
    for i in range(len(settings.groups))
]
groups.append(scratchpad)


def go_to_group(name: str):
    def _inner(qtile):
        if len(qtile.screens) == 1:
            qtile.groups_map[name].toscreen(toggle=True)
            return

        if name in ["social", "settings", "media"]:
            qtile.focus_screen(0)
            qtile.groups_map[name].toscreen()
        elif name in ["www", "etc"]:
            qtile.focus_screen(1)
            qtile.groups_map[name].toscreen()
        elif name in ["coding"]:
            qtile.focus_screen(2)
            qtile.groups_map[name].toscreen()

    return _inner


keys_to_be_inserted = []
for i, group in enumerate(settings.groups, 1):
    name = group.name
    keys_to_be_inserted.extend(
        [
            Key(
                [settings.keymaps.mod],
                str(i),
                lazy.function(go_to_group(name)),
                desc=f"Go to group `{name}`",
            ),
            Key(
                [settings.keymaps.mod, "shift"],
                str(i),
                lazy.window.togroup(name),
                desc=f"Move window to group `{name}`",
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
