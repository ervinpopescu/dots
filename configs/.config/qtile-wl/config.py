import json
import os

from libqtile.backend.wayland.inputs import InputConfig

from modules import (
    alt_tab_hooks,
    apps_hooks,
    floating_layout,
    groups,
    keys,
    layouts,
    misc_hooks,
    mouse,
    screens,
    window_rules_hooks,
)
from modules.settings import config_path, widget_defaults

assert alt_tab_hooks
assert apps_hooks
assert window_rules_hooks
assert misc_hooks

assert widget_defaults
assert layouts
assert floating_layout
assert keys
assert mouse
assert groups
# assert screens

with open(os.path.join(config_path, "json", "config.json")) as f:
    config = json.load(f)
    for key, val in config.items():
        if key != "theme":
            exec(f"{key}=val")


def focus_on_window_activation(win):
    return "feh_thumbnail" not in win.get_wm_class()


# When using the Wayland backend, this can be used to configure input devices.
wl_input_rules = {
    "type:touchpad": InputConfig(
        pointer_accel=0.5,
        drag=True,
        natural_scroll=True,
        tap=True,
        middle_emulation=True,
    ),
}
