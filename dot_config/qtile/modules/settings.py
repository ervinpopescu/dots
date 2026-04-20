import json
import math
import os
import pathlib
from os import path

from libqtile import qtile
from libqtile.utils import rgb

from modules.models import Settings

# from qtile_extras.layout.decorations.borders import RoundedCorners


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


# notify2.init("qtile config")
# qtile: Qtile
try:
    qtile_info = qtile.qtile_info()  # type: ignore
except AttributeError:
    qtile_info = {}

if len(qtile_info) != 0:
    config_path = str(pathlib.Path(qtile_info["config_path"]).parent.resolve())
else:
    config_path = str(pathlib.Path(__file__).parent.parent.resolve())

colors = load_theme()

with open(os.path.join(config_path, "json", "settings.json")) as f:
    settings_dict = json.load(f)
    settings = Settings(**settings_dict)

bar_bg = "2e344000"
decor_bg = colors["bg0"]


def rounded_corners_bg0(ctx, bw, width, height):
    radius = int(bw / 2)
    degrees = math.pi / 180.0
    ctx.new_sub_path()
    ctx.arc(width - bw, bw, radius, -90 * degrees, 0 * degrees)
    ctx.arc(width - bw, height - bw, radius, 0 * degrees, 90 * degrees)
    ctx.arc(bw, height - bw, radius, 90 * degrees, 180 * degrees)
    ctx.arc(bw, bw, radius, 180 * degrees, 270 * degrees)
    ctx.close_path()

    ctx.set_line_width(bw)
    ctx.set_source_rgba(*rgb(colors["bg0"]))  # type: ignore
    ctx.stroke()


def rounded_corners_purple(ctx, bw, width, height):
    radius = int(bw / 2)
    degrees = math.pi / 180.0

    ctx.new_sub_path()
    ctx.arc(width - bw, bw, radius, -90 * degrees, 0 * degrees)
    ctx.arc(width - bw, height - bw, radius, 0 * degrees, 90 * degrees)
    ctx.arc(bw, height - bw, radius, 90 * degrees, 180 * degrees)
    ctx.arc(bw, bw, radius, 180 * degrees, 270 * degrees)
    ctx.close_path()

    ctx.set_line_width(bw)
    ctx.set_source_rgba(*rgb(colors["purple"]))  # type: ignore
    ctx.stroke()


layout_defaults = dict(
    margin=settings.margin_size,
    border_width=4,
    border_normal=colors["bg0"],
    border_focus=colors["purple"],
)
widget_defaults = {
    "font": "Font Awesome 6 Free Solid",
    "fontsize": settings.font_size,
    "padding": 6,
}
extension_defaults = widget_defaults.copy()
