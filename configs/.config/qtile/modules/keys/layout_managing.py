from libqtile.config import Key
from libqtile.lazy import lazy

from modules.settings import settings

layout_managing_keys = [
    Key(
        [settings["keymaps"]["mod"]],
        "n",
        lazy.layout.normalize(),
        lazy.layout.reset(),
        desc="(Normalize || Reset) layout",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "Tab",
        lazy.next_layout(),
        desc="Next layout",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "Tab",
        lazy.prev_layout(),
        desc="Previous layout",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "s",
        lazy.layout.toggle_split().when(layout="bsp"),
        desc="Toggle bsp split",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "Up",
        lazy.layout.shuffle_up(),
        desc="Shuffle up",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "Left",
        lazy.layout.shuffle_left(),
        desc="Shuffle left",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "Right",
        lazy.layout.shuffle_right(),
        desc="Shuffle right",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "Down",
        lazy.layout.shuffle_down(),
        desc="Shuffle down",
    ),
]
