import json
import os

from libqtile.backend.wayland.inputs import InputConfig
from modules import (
    apps_hooks,
    floating_layout,
    groups,
    idle_inhibitors,
    idle_timers,
    keys,
    layouts,
    misc_hooks,
    mouse,
    qalttab_hooks,
    screens,
    window_rules_hooks,
)
from modules.settings import config_path, widget_defaults

assert qalttab_hooks
assert apps_hooks
assert window_rules_hooks
assert misc_hooks
assert idle_inhibitors
assert idle_timers
assert widget_defaults
assert layouts
assert floating_layout
assert keys
assert mouse
assert groups
assert screens

with open(os.path.join(config_path, "json", "config.json")) as f:
    config = json.load(f)
    for key, val in config.items():
        if key != "theme":
            globals()[key] = val


wl_input_rules = {
    "type:touchpad": InputConfig(
        accel_profile="adaptive",
        pointer_accel=0.2,
        drag=True,
        natural_scroll=True,
        tap=True,
        middle_emulation=True,
    ),
}
