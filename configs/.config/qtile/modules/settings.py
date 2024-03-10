import json
import os
import pathlib
from os import path

import notify2
from libqtile import qtile
from libqtile.core.manager import Qtile


def load_theme():
    theme = "catppuccin"

    config = path.join(config_path, "json", "config.json")
    if path.isfile(config):
        with open(config) as f:
            theme = json.load(f)["theme"]
    else:
        with open(config, "w") as f:
            f.write(f'{{"theme": "{theme}"}}\n')

    theme_file = path.join(config_path, "themes", f"{theme}.json")
    if not path.isfile(theme_file):
        raise FileNotFoundError(f'"{theme_file}" does not exist')

    with open(path.join(theme_file)) as f:
        return json.load(f)


notify2.init("qtile config")
qtile: Qtile
qtile_info = qtile.qtile_info()
if len(qtile_info) != 0:
    config_path = str(pathlib.Path(qtile_info["config_path"]).parent.resolve())
else:
    config_path = str(pathlib.Path(__file__).parent.parent.resolve())

colors = load_theme()
with open(os.path.join(config_path, "json", "settings.json")) as f:
    settings: dict = json.load(f)

bar_bg = "2e344000"
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
