import json
import math
import os
import pathlib

# import notify2
from libqtile import qtile
from libqtile.config import Match
from libqtile.utils import rgb
from qtile_extras.layout.decorations.borders import ConditionalBorderWidth, CustomBorder

from modules.models import Settings

# notify2.init("qtile-wl-cfg")


def load_theme(config_path):
    theme = settings.theme
    theme_file = os.path.join(config_path, "themes", f"{theme}.json")
    if not os.path.isfile(theme_file):
        raise FileNotFoundError(f'"{theme_file}" does not exist')

    with open(theme_file) as f:
        return json.load(f)


try:
    qtile_info = qtile.qtile_info()  # type: ignore
    config_path = str(pathlib.Path(qtile_info["config_path"]).parent.resolve())
except AttributeError:
    config_path = str(pathlib.Path(__file__).parent.parent.resolve())

with open(os.path.join(config_path, "json", "settings.json")) as f:
    settings = Settings(**json.load(f))
colors = load_theme(config_path)

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
    border_width=ConditionalBorderWidth(
        matches=[
            (
                Match(title="qalttab"),
                0,
            )
        ],
        default=4,
    ),
    border_normal=CustomBorder(func=rounded_corners_bg0),
    border_focus=CustomBorder(func=rounded_corners_purple),
)
widget_defaults = settings.widget_defaults.model_dump()
extension_defaults = widget_defaults.copy()
