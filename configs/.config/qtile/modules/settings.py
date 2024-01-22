import json
import os

from modules.path import config_path
from modules.theme import colors

with open(os.path.join(config_path, "json", "settings.json")) as f:
    settings: dict = json.load(f)

bar_bg = "00000000"
decor_bg = colors["bg0"]
layout_defaults = dict(
    margin=settings["margin_size"],
    border_width=5,
    border_focus=colors["purple"],
    border_normal=colors["bg0"],
)
widget_defaults = {
    "font": "Font Awesome 6 Free Solid",
    "fontsize": settings["font_size"],
    "padding": 6,
}
extension_defaults = widget_defaults.copy()
