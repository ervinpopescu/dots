from libqtile.config import Key
from libqtile.lazy import lazy

from modules.settings import settings

window_managing_keys = [
    Key(
        [settings["cmds"]["mod"]],
        "e",
        lazy.window.toggle_maximize(),
        desc="Make window maximized",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "e",
        lazy.window.toggle_fullscreen(),
        desc="Make window fullscreen",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "f",
        lazy.window.toggle_floating(),
        desc="Make window floating",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "b",
        lazy.window.bring_to_front(),
        desc="Bring window to front",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "q",
        lazy.window.kill(),
        desc="Kill window",
    ),
]
