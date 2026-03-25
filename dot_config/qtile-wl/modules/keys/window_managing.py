from libqtile.config import Key
from libqtile.lazy import lazy

from modules.popups import close_app_with_warning_window
from modules.settings import settings

window_managing_keys = [
    Key(
        [settings["keymaps"]["mod"]],
        "e",
        lazy.window.toggle_maximize(),
        desc="Make window maximized",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "e",
        lazy.window.toggle_fullscreen(),
        desc="Make window fullscreen",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "f",
        lazy.window.toggle_floating(),
        desc="Make window floating",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "b",
        lazy.window.bring_to_front(),
        desc="Bring window to front",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "q",
        lazy.window.kill(),
        desc="Kill window",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "w",
        close_app_with_warning_window(),
        desc="Kill window",
    ),
]
