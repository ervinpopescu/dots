#!/bin/python

import io
import json
import pathlib
from matplotlib.colors import colorConverter
import os
import sys
from libqtile.command.client import InteractiveCommandClient
from PIL import Image, ImageDraw
from libqtile.backend.x11 import xcbq
import gi

gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import GdkPixbuf, Gdk

c = InteractiveCommandClient()
qtile_info = c.qtile_info()
if len(qtile_info) != 0:
    config_path = str(pathlib.Path(qtile_info["config_path"]).parent.resolve())
else:
    config_path = str(pathlib.Path(__file__).parent.parent.resolve())
with open(os.path.join(config_path, "json", "settings.json")) as f:
    settings: dict = json.load(f)
systray_screen_index = c.widget["systray"].screen.info()["index"]
systray_screen = xcbq.Connection(os.environ.get("DISPLAY")).pseudoscreens[
    systray_screen_index
]
screen = dict(
    x=systray_screen.x,
    y=systray_screen.y,
    width=systray_screen.width,
    height=systray_screen.height,
)

systray_values = dict(
    length=c.widget["systray"].info()["widget"]["length"],
    offset=c.widget["systray"].info()["widget"]["offset"],
    height=c.bar["top"].info()["height"],
)

systray_position = dict(
    x0=systray_values["offset"] + 30,
    y0=settings["margin_size"],
    x1=systray_values["offset"] + systray_values["length"] + 30,
    y1=systray_values["height"] + settings["margin_size"],
)

# NOTE: This is how `nitrogen` does the `zoom_fill` on the image
orig = GdkPixbuf.Pixbuf.new_from_file(sys.argv[1])

winw = screen["width"]
winh = screen["height"]

orig_w, orig_h = (orig.get_width(), orig.get_height())

# what if we expand it to fit the screen width?
x = 0
w = winw
h = winw * orig_h / orig_w
y = (h - winh) / 2

if h < winh:
    # the image isn't tall enough that way!
    # expand it to fit the screen height
    y = 0
    w = winh * orig_w / orig_h
    h = winh
    x = (w - winw) / 2

tmp = orig.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
pixbuf_out = GdkPixbuf.Pixbuf.new(
    orig.get_colorspace(),
    orig.get_has_alpha(),
    orig.get_bits_per_sample(),
    winw,
    winh,
)

# use passed bg color
r, g, b = colorConverter.to_rgb("#1E1E2E")
pixbuf_out.fill(0x1E1E2EFF)

# // copy it in
tmp.copy_area(x, y, winw, winh, pixbuf_out, 0, 0)

result, data = pixbuf_out.save_to_bufferv(
    "png",
    None,
    None,
)
if result:
    image_io = io.BytesIO(data)
    image = Image.open(image_io)
else:
    exit(1)

draw = ImageDraw.Draw(image, "RGBA")
draw.rounded_rectangle(
    [
        (
            systray_position["x0"],
            systray_position["y0"],
        ),
        (
            systray_position["x1"],
            systray_position["y1"],
        ),
    ],
    radius=20,
    fill="#1E1E2E",
    outline="#1E1E2E",
    width=4,
)
image.save(
    os.path.join(
        os.environ.get("XDG_DATA_HOME", os.path.expanduser("~") + "/.local/share"),
        "wallpaper",
        "output.png",
    ),
    "PNG",
)
