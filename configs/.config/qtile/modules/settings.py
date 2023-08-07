import json
import os

from modules.path import config_path
from modules.theme import colors

with open(os.path.join(config_path, "json", "settings.json")) as f:
    config = json.load(f)
    for key, val in config.items():
        exec(f"{key}=val")

bar_bg = "00000000"
decor_bg = colors["bg0"]
layout_defaults = dict(
    margin=margin_size,  # pyright: ignore
    border_width=5,
    border_focus=colors["purple"],
    border_normal=colors["bg0"],
)
