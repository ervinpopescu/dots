from libqtile.config import Key
from libqtile.lazy import lazy

from modules.functions import (
    decrease_gaps,
    increase_gaps,
    set_layout_all,
    set_layout_current,
    toggle_gaps,
)
from modules.settings import config_path, settings
from modules.widget_names import WIDGETBOX_1, WIDGETBOX_2

qtile_keys = [
    Key(
        [settings["keymaps"]["mod"]],
        "v",
        lazy.validate_config(),
        desc="Validate config",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "r",
        lazy.reload_config(),
        lazy.spawn(f"{config_path}/scripts/set_spotify_size.py"),
        desc="Reload qtile config",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "r",
        lazy.restart(),
        lazy.spawn(f"{config_path}/scripts/set_spotify_size.py"),
        desc="Restart qtile",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "q",
        lazy.shutdown(),
        desc="Shutdown qtile",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "a",
        lazy.hide_show_bar(),
        desc="Hide/show all bars",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "x",
        # lazy.widget["widgetbox"].toggle(),
        lazy.widget[WIDGETBOX_1].toggle(),
        lazy.widget[WIDGETBOX_2].toggle(),
        desc="Toggle WidgetBoxesk",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "z",
        toggle_gaps(),
        desc="Toggle gaps",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "equal",
        increase_gaps(),
        desc="Increase gaps",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "minus",
        decrease_gaps(),
        desc="Decrease gaps",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "m",
        set_layout_all(),
        desc="Toggle max/default layout on all groups",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "n",
        set_layout_current(),
        desc="Toggle max/default layout on current group",
    ),
]
