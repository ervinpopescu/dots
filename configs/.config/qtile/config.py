import json
import os

from modules import (
    extension_defaults,
    floating_layout,
    groups,
    keys,
    layouts,
    mouse,
    screens,
    widget_defaults,
)
from modules.settings import config_path
import modules.hooks.apps as apps
import modules.hooks.layout as layout
import modules.hooks.misc as misc
import modules.hooks.session as session

assert apps
assert layout
assert misc
assert session
# import modules.hooks.swallow

assert floating_layout
assert groups
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
