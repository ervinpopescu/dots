# Copyright (c) 2010 Aldo Cortesi
# Copyright (c) 2010, 2014 dequis
# Copyright (c) 2012 Randall Ma
# Copyright (c) 2012-2014 Tycho Andersen
# Copyright (c) 2012 Craig Barnes
# Copyright (c) 2013 horsik
# Copyright (c) 2013 Tao Sauvage
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import os

from libqtile.backend.wayland.inputs import InputConfig

from modules import (
    groups,
    keys,
    layouts,
    mouse,
    screens,
)
from modules.hooks import apps as apps_hooks
from modules.hooks import layout as layout_hooks
from modules.hooks import misc as misc_hooks
from modules.layouts import floating_layout
from modules.settings import config_path, widget_defaults

assert floating_layout
assert groups
assert keys
assert layouts
assert mouse
assert screens
assert widget_defaults

assert apps_hooks
assert layout_hooks
assert misc_hooks

with open(os.path.join(config_path, "json", "config.json")) as f:
    config = json.load(f)
    for key, val in config.items():
        if key != "theme":
            exec(f"{key}=val")


def focus_on_window_activation(win):
    return "feh_thumbnail" not in win.get_wm_class()


# When using the Wayland backend, this can be used to configure input devices.
wl_input_rules = {
    "type:touchpad": InputConfig(
        pointer_accel=0.5,
        drag=True,
        natural_scroll=True,
        tap=True,
        middle_emulation=True,
    ),
}

# xcursor theme (string or None) and size (integer) for Wayland backend
