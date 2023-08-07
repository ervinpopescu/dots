from libqtile.config import Key
from libqtile.lazy import lazy

from modules.settings import cmds

layout_managing_keys = [
    Key(
        [cmds["mod"]],
        "n",
        lazy.layout.normalize(),
        lazy.layout.reset(),
        desc="(Normalize || Reset) layout",
    ),
    Key(
        [cmds["mod"]],
        "Tab",
        lazy.next_layout(),
        desc="Next layout",
    ),
    Key(
        [cmds["mod"], "shift"],
        "Tab",
        lazy.prev_layout(),
        desc="Previous layout",
    ),
    Key(
        [cmds["mod"]],
        "h",
        lazy.layout.toggle_split().when(layout="bsp"),
        desc="Toggle bsp split",
    ),
    Key(
        [cmds["mod"], "shift"],
        "Up",
        lazy.layout.shuffle_up(),
        desc="Shuffle up",
    ),
    Key(
        [cmds["mod"], "shift"],
        "Left",
        lazy.layout.shuffle_left(),
        desc="Shuffle left",
    ),
    Key(
        [cmds["mod"], "shift"],
        "Right",
        lazy.layout.shuffle_right(),
        desc="Shuffle right",
    ),
    Key(
        [cmds["mod"], "shift"],
        "Down",
        lazy.layout.shuffle_down(),
        desc="Shuffle down",
    ),
]
