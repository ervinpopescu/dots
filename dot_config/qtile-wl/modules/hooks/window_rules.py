import json
import os
from typing import TYPE_CHECKING, Optional, cast

import json5  # type: ignore
import libqtile.core.manager
from libqtile import hook, qtile
from libqtile.backend.base import Window  # type: ignore
from libqtile.log_utils import logger

from modules.matches import matches
from modules.settings import config_path, settings


def get_screen_width_safe() -> int:
    default_width = 1920
    if not TYPE_CHECKING and hasattr(qtile, "core") and hasattr(qtile.core, "running") and qtile.core.running:
        try:
            _core = cast(libqtile.core.manager.Core, qtile.core)
            screen_info = _core.get_output_info()
            if screen_info:
                return max([output.width for output in screen_info])
        except Exception:
            pass
    return default_width


@hook.subscribe.client_new
def window_rules(client: Window):
    with open(os.path.join(config_path, "json", "window_rules.json"), "r") as f:
        rules: list[dict] = json5.loads(f.read())  # type: ignore
    logger.debug(
        "%s",
        json.dumps(
            rules,
            indent=2,
        ),
    )
    logger.debug(
        "%s",
        json.dumps(
            matches,
            indent=2,
        ),
    )
    wm_class = client.get_wm_class()
    if wm_class:
        wm_class = wm_class[0]
    role: Optional[str] = client.get_wm_role()
    if not role:
        role = None
    name: Optional[str] = client.name
    if not name:
        name = None

    logger.info("wm_class: %s, role: %s, name: %s", wm_class, role, name)
    for group, wm_classes in matches.items():
        if wm_class in wm_classes:
            logger.info("wm_class recognized in matches")
            client.togroup(group)
            client.group.toscreen(toggle=False)  # type: ignore

    for win in rules:
        rules_wm_class = win["wm_class"]
        rules_name = win.get("name", None)
        if rules_wm_class == wm_class and rules_name == name:
            if (
                "set_position_floating" in win["rules"]
                and rules_wm_class == "gsimplecal"
            ):
                logger.info(
                    f"set_position_floating: class:{rules_wm_class},name:{rules_name}"
                )
                client.set_position_floating(
                    x=get_screen_width_safe()
                    - win["rules"]["w"]  # type: ignore
                    - settings.margin_size
                    - 5,
                    y=settings.bar_height + 2 * settings.margin_size,
                )

            if "set_size_floating" in win["rules"]:
                logger.info(
                    f"set_size_floating: class:{rules_wm_class},name:{rules_name}"
                )
                client.set_size_floating(w=win["rules"]["w"], h=win["rules"]["h"])

            if "toggle_floating" in win["rules"]:
                logger.info(
                    f"toggle_floating: class:{rules_wm_class},name:{rules_name}"
                )
                client.toggle_floating()

            if "center" in win["rules"]:
                logger.info(f"center: class:{rules_wm_class},name:{rules_name}")
                client.center()

            if "keep_above" in win["rules"]:
                logger.info(f"keep_above: class:{rules_wm_class},name:{rules_name}")
                client.keep_above()

            if "toggle_fullscreen" in win["rules"]:
                logger.info(
                    f"toggle_fullscreen: class:{rules_wm_class},name:{rules_name}"
                )
                client.toggle_fullscreen()

            return
