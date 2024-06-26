import os
from time import sleep

import json5
from libqtile import hook, qtile
from libqtile.backend.base import Window
from libqtile.core.manager import Qtile

from modules.matches import matches
from modules.settings import config_path, settings

qtile: Qtile

with open(os.path.join(config_path, "json", "window_rules.json"), "r") as f:
    rules: dict = json5.loads(f.read())


@hook.subscribe.client_new
@hook.subscribe.client_managed
def resize_and_move_client(client: Window):
    wm_class = client.window.get_wm_class()
    if wm_class:
        wm_class = wm_class[0]
    else:
        wm_class = None
    role = client.get_wm_role()
    if not role:
        role = None
    name = client.name
    if not name:
        name = None

    for group, wm_classes in matches.items():
        if wm_class in wm_classes:
            client.togroup(group)
            client.group.toscreen(toggle=False)
            return

    for key, win in rules.items():
        if key in [wm_class, role, name]:
            if "set_position_floating" in win and key == "gsimplecal":
                client.set_position_floating(
                    x=qtile.core.get_screen_info()[0][2]
                    - win["w"]
                    - settings["margin_size"]
                    - 5,
                    y=settings["bar_height"] + 2 * settings["margin_size"],
                )
                return

            if "set_size_floating" in win:
                if key == "blueman-manager":
                    sleep(3)
                client.set_size_floating(w=win["w"], h=win["h"])
                return

            if "toggle_floating" in win:
                client.toggle_floating()
                return

            if "center" in win:
                client.center()
                return

            if "keep_above" in win:
                client.keep_above()
                return
