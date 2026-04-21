import os

import jsonpickle  # type: ignore  # noqa: S301 - existing dep for keys.json serialization
from libqtile import hook
from libqtile.config import EzKey, Group, Key
from libqtile.lazy import lazy

from extras.mutablescratch import MutableScratch
from modules.groups.scratchpad import scratchpad
from modules.keys import keys
from modules.settings import config_path, settings

_groups_by_name = {g.name: g for g in settings.groups}


def go_to_group(name: str):
    def _inner(qtile):
        if len(qtile.screens) == 1:
            qtile.groups_map[name].toscreen(toggle=True)
            return
        else:
            screen = _groups_by_name[name].screen_affinity
            qtile.focus_screen(screen)
            qtile.groups_map[name].toscreen()

    return _inner


groups = []
keys_to_be_inserted = []
for i, g in enumerate(settings.groups, 1):
    groups.append(
        Group(
            name=g.name,
            layout=g.layout,
            label=g.label,
            screen_affinity=g.screen_affinity,
            layout_opts=None,
        )
    )
    keys_to_be_inserted.extend(
        [
            Key(
                [settings.keymaps.mod],
                str(i),
                lazy.function(go_to_group(g.name)),
                desc=f"Go to group `{g.name}`",
            ),
            Key(
                [settings.keymaps.mod, "shift"],
                str(i),
                lazy.window.togroup(g.name),
                desc=f"Move window to group `{g.name}`",
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
