import json
import os

from modules import (
    extension_defaults,
    floating_layout,
    groups,
    hooks,
    keys,
    layouts,
    mouse,
    screens,
    widget_defaults,
)
from modules.path import config_path

assert floating_layout
assert groups
assert hooks
assert keys
assert layouts
assert mouse
assert screens
assert widget_defaults
assert extension_defaults

with open(os.path.join(config_path, "json", "config.json")) as f:
    config = json.load(f)
    for key, val in config.items():
        if key != "theme":
            exec(f"{key}=val")
