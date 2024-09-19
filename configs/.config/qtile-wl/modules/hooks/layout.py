import os

import json5
from libqtile import hook, qtile
from libqtile.backend.base import Window  # type: ignore
from libqtile.core.manager import Qtile
from libqtile.log_utils import logger

from modules.matches import matches
from modules.settings import config_path, settings

qtile: Qtile


@hook.subscribe.client_new
def resize_and_move_client(client: Window):
    # qtile.info()
    with open(os.path.join(config_path, "json", "window_rules.json"), "r") as f:
        rules: dict = json5.loads(f.read())  # type: ignore
    logger.info(rules)
    logger.info(matches)

    wm_class = client.get_wm_class()
    if wm_class:
        wm_class = wm_class[0]
    role = client.get_wm_role()
    if not role:
        role = None
    name = client.name
    if not name:
        name = None

    logger.info("wm_class: %s, role: %s, name: %s", wm_class, role, name)
    for group, wm_classes in matches.items():
        logger.info(wm_class in wm_classes)
        if wm_class in wm_classes:
            logger.info("wm_class recognized in matches")
            client.togroup(group)
            client.group.toscreen(toggle=False)  # type: ignore

    for key, win in rules.items():
        if key in [wm_class, role, name]:
            if "set_position_floating" in win and key == "gsimplecal":
                client.set_position_floating(
                    x=qtile.core.get_screen_info()[0][2]  # type: ignore
                    - win["w"]
                    - settings["margin_size"]
                    - 5,
                    y=settings["bar_height"] + 2 * settings["margin_size"],
                )

            # if "set_size_floating" in win:
            #     if key == "blueman-manager":
            #
            #         async def sleep_and_set_size(win):
            #             await asyncio.sleep(3)
            #             client.set_size_floating(w=win["w"], h=win["h"])
            #
            #         create_task(sleep_and_set_size(win))

            if "toggle_floating" in win:
                client.toggle_floating()

            if "center" in win:
                client.center()

            if "keep_above" in win:
                client.keep_above()

            return
