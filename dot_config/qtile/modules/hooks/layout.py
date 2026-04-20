import asyncio
import os

import json5
from libqtile import hook, qtile
from libqtile.backend.base import Window
from libqtile.utils import create_task

from modules.matches import matches
from modules.settings import config_path, settings


@hook.subscribe.client_new
@hook.subscribe.client_managed
def resize_and_move_client(client: Window):
    with open(os.path.join(config_path, "json", "window_rules.json"), "r") as f:
        rules: dict = json5.loads(f.read())

    wm_class = client.window.get_wm_class()  # type: ignore[attr-defined]
    if wm_class and len(wm_class) == 2:
        wm_class_0 = wm_class[0]
        wm_class_1 = wm_class[1]
    else:
        wm_class_0 = None
        wm_class_1 = None
        wm_class = None
    role: str | None = client.get_wm_role()  # type: ignore[assignment]
    if not role:
        role = None
    name: str | None = client.name
    if not name:
        name = None

    for group, wm_classes in matches.items():
        if wm_class_0 in wm_classes or wm_class_1 in wm_classes:
            client.togroup(group)
            if client.group is not None:
                client.group.toscreen(toggle=False)

    for key, win in rules.items():
        if key in [wm_class_0, wm_class_1, role, name]:
            if "set_position_floating" in win and key == "gsimplecal":
                client.set_position_floating(
                    x=qtile.core.get_output_info()[0][2] - win["w"] - settings.margin_size - 5,  # type: ignore[attr-defined]
                    y=settings.bar_height + 2 * settings.margin_size,
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
