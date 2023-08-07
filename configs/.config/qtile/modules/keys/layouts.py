from libqtile.config import Key
from libqtile.lazy import lazy

from modules.settings import cmds

layouts_keys = [
    Key(
        [cmds["mod"], "control"],
        "Right",
        lazy.layout.grow().when(layout=["monadwide", "monadtall", "monadthreecol"]),
        lazy.layout.grow_right().when(layout=["bsp", "columns"]),
        lazy.layout.increase_ratio().when(layout="spiral"),
        desc="Grow (monad*) || Grow right (bsp&col) || Increase ratio (spiral)",
    ),
    Key(
        [cmds["mod"], "control"],
        "Left",
        lazy.layout.shrink().when(layout=["monadwide", "monadtall" or "monadthreecol"]),
        lazy.layout.grow_left().when(layout=["bsp", "columns"]),
        lazy.layout.decrease_ratio().when(layout="spiral"),
        desc="Shrink (monad*) || Grow left (bsp&col) || Decrease ratio (spiral)",
    ),
    Key(
        [cmds["mod"], "control"],
        "Up",
        lazy.layout.grow().when(layout=["monadwide", "monadtall", "monadthreecol"]),
        lazy.layout.grow_up().when(layout=["bsp", "columns"]),
        desc="Grow (monad*) || Grow up (bsp&col)",
    ),
    Key(
        [cmds["mod"], "control"],
        "Down",
        lazy.layout.shrink().when(layout=["monadwide", "monadtall", "monadthreecol"]),
        lazy.layout.grow_down().when(layout=["bsp", "columns"]),
        desc="Shrink (monad*) || Grow down (bsp&col)",
    ),
]
