import json
import math
import os
import pathlib

from libqtile import qtile
from libqtile.utils import rgb

from modules.models import Settings

DEFAULT_CONFIG = {
    "auto_fullscreen": True,
    "auto_minimize": True,
    "bring_front_click": "floating_only",
    "cursor_warp": True,
    "floats_kept_above": True,
    "follow_mouse_focus": True,
    "theme": "catppuccin",
    "wmname": "LG3D",
    "x11_fake_transparency": True,
}


def load_runtime_config(config_path):
    config_file = os.path.join(config_path, "json", "config.json")
    try:
        with open(config_file) as f:
            return json.load(f)
    except FileNotFoundError:
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        try:
            with open(config_file, "x") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
                f.write("\n")
            return DEFAULT_CONFIG.copy()
        except FileExistsError:
            with open(config_file) as f:
                return json.load(f)


def load_theme(config_path):
    theme = settings.theme
    theme_file = os.path.join(config_path, "themes", f"{theme}.json")
    if not os.path.isfile(theme_file):
        raise FileNotFoundError(f'"{theme_file}" does not exist')
    try:
        with open(theme_file) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f'could not load theme "{theme}"') from error


try:
    qtile_info = qtile.qtile_info()  # type: ignore
    config_path = str(pathlib.Path(qtile_info["config_path"]).parent.resolve())
except AttributeError:
    config_path = str(pathlib.Path(__file__).parent.parent.resolve())

try:
    with open(os.path.join(config_path, "json", "settings.json")) as f:
        settings = Settings(**json.load(f))
except (OSError, json.JSONDecodeError, ValueError) as error:
    raise RuntimeError("could not load Qtile settings") from error
colors = load_theme(config_path)

bar_bg = "2e344000"
decor_bg = colors["bg0"]


def rounded_corners_bg0(ctx, bw, width, height):
    radius = bw // 2
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
    radius = bw // 2
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
widget_defaults = settings.widget_defaults.model_dump()
extension_defaults = widget_defaults.copy()
