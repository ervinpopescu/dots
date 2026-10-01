import json
import os

from libqtile import confreader
from modules import (  # noqa: F401
    extension_defaults,
    floating_layout,
    generate_screens,
    groups,
    keys,
    layouts,
    mouse,
    widget_defaults,
)
from modules.hooks import apps as apps_hooks
from modules.hooks import layout as layout_hooks
from modules.hooks import misc as misc_hooks
from modules.settings import config_path

assert floating_layout
assert groups
assert keys
assert layouts
assert mouse
assert widget_defaults
assert extension_defaults

assert apps_hooks
assert layout_hooks
assert misc_hooks

with open(os.path.join(config_path, "json", "config.json")) as f:
    config = json.load(f)
    for key, val in config.items():
        if key != "theme":
            globals()[key] = val


focus_on_window_activation = "smart"

# Fallback for Qtile < 0.35 which does not support generate_screens
if "generate_screens" not in getattr(confreader.Config, "__annotations__", {}):
    from modules.screens import screens  # noqa: F401
