import pathlib

from libqtile import qtile
from libqtile.config import Key
from libqtile.lazy import lazy

from modules.functions import (
    decrease_gaps,
    increase_gaps,
    set_layout_all,
    set_layout_current,
    toggle_gaps,
)
from modules.path import config_path
from modules.settings import settings

qtile_keys = [
    Key(
        [settings["cmds"]["mod"]],
        "v",
        lazy.validate_config(),
        desc="Validate config",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "r",
        lazy.reload_config(),
        lazy.spawn(f"{config_path}/scripts/set_spotify_size.py"),
        # lazy.hide_show_bar("bottom"),
        desc="Reload qtile config",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "r",
        lazy.restart(),
        lazy.spawn(f"{config_path}/scripts/set_spotify_size.py"),
        desc="Restart qtile",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "q",
        lazy.shutdown(),
        desc="Shutdown qtile",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "a",
        lazy.hide_show_bar(),
        desc="Hide/show all bars",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "x",
        lazy.widget["widgetbox"].toggle(),
        desc="Toggle only WidgetBox",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "z",
        toggle_gaps(),
        desc="Toggle gaps",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "equal",
        increase_gaps(),
        desc="Increase gaps",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "minus",
        decrease_gaps(),
        desc="Decrease gaps",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "m",
        set_layout_all(),
        desc="Toggle max/default layout on all groups",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "n",
        set_layout_current(),
        desc="Toggle max/default layout on current group",
    ),
]
