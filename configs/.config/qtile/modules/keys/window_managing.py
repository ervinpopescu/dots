from libqtile.config import Key
from libqtile.lazy import lazy

from modules.settings import cmds

window_managing_keys = [
    Key(
        [cmds["mod"]],
        "e",
        lazy.window.toggle_maximize(),
        desc="Make window maximized",
    ),
    Key(
        [cmds["mod"], "shift"],
        "e",
        lazy.window.toggle_fullscreen(),
        desc="Make window fullscreen",
    ),
    Key(
        [cmds["mod"], "shift"],
        "f",
        lazy.window.toggle_floating(),
        desc="Make window floating",
    ),
    Key(
        [cmds["mod"], "shift"],
        "b",
        lazy.window.bring_to_front(),
        desc="Bring window to front",
    ),
    Key(
        [cmds["mod"]],
        "q",
        lazy.window.kill(),
        desc="Kill window",
    ),
]
