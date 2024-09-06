import os
import asyncio

import json5
from libqtile import hook, qtile
from libqtile.utils import create_task
from libqtile.log_utils import logger
from libqtile.backend.base import Window
from libqtile.core.manager import Qtile

from modules.matches import matches
from modules.settings import config_path, settings

qtile: Qtile

@hook.subscribe.client_new
@hook.subscribe.client_managed
def resize_and_move_client(client: Window):
    with open(os.path.join(config_path, "json", "window_rules.json"), "r") as f:
        rules: dict = json5.loads(f.read())

    wm_class = client.window.get_wm_class()
    if wm_class and len(wm_class) == 2:
        wm_class_0 = wm_class[0]
        wm_class_1 = wm_class[1]
    else:
        wm_class_0 = None
        wm_class_1 = None
        wm_class = None
    role = client.get_wm_role()
    if not role:
        role = None
    name = client.name
    if not name:
        name = None

    for group, wm_classes in matches.items():
        if wm_class_0 in wm_classes or wm_class_1 in wm_classes:
            client.togroup(group)
            client.group.toscreen(toggle=False)

    for key, win in rules.items():
        if key in [wm_class_0, wm_class_1, role, name]:
            if "set_position_floating" in win and key == "gsimplecal":
                client.set_position_floating(
                    x=qtile.core.get_screen_info()[0][2] - win["w"] - settings["margin_size"] - 5,
                    y=settings["bar_height"] + 2 * settings["margin_size"],
                )

            if "set_size_floating" in win:
                if key == "blueman-manager":
                    async def sleep_and_set_size(win):
                        asyncio.sleep(3)
                        client.set_size_floating(w=win["w"], h=win["h"])
                    create_task(sleep_and_set_size(win))

            if "toggle_floating" in win:
                client.toggle_floating()

            if "center" in win:
                client.center()

            if "keep_above" in win:
                client.keep_above()

            return
