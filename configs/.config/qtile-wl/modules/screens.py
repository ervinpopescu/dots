import json

from libqtile import bar, hook, qtile
from libqtile.config import Screen
from libqtile.log_utils import logger

from modules.settings import bar_bg, settings
from modules.widgets import *  # noqa: F403

bh = settings["bar_height"]
ms = settings["margin_size"]


def statusbar(widgets, margin, size):
    return bar.Bar(
        widgets,
        size=size,
        margin=margin,
        background=bar_bg,
    )


# @hook.subscribe.screens_reconfigured
# def modify_screens():
#     if len(qtile.get_screens()) == 3:
#         # find screen with bar, probably left most one which coincidentally is
#         # rotated
#         screens = qtile.screens
#         bars = [scr.bottom for scr in screens]
#         logger.info(bars)
#         screen_with_bar = [scr for scr in screens if scr.bottom is not None][0]
#
#         # laptop screen should be the primary
#         laptop_screen = screens[2]
#         logger.info("laptop screen: %s", laptop_screen)
#         laptop_screen.bottom = screen_with_bar.bottom
#         logger.info("laptop screen bottom: %s", laptop_screen.bottom)
#         screen_with_bar.bottom = None
#         laptop_screen.bottom.draw()

screens = [
    # Screen(
    #     bottom=statusbar(
    #         widgets=widgets_2,  # noqa: F405
    #         size=bh * 2 // 3,
    #         margin=[
    #             0,
    #             ms - 5,
    #             ms - 5,
    #             ms - 5,
    #         ],
    #     ),
    #     # needs https://github.com/tych0/qtile/commit/2074b9a196 and further
    #     # work in wayland
    #     # serial="CN41010NQC",
    # ),
    # Screen(
    #     bottom=statusbar(
    #         widgets=widgets_3,  # noqa: F405
    #         size=bh * 2 // 3,
    #         margin=[
    #             0,
    #             ms - 5,
    #             ms - 5,
    #             ms - 5,
    #         ],
    #     ),
    #     # needs https://github.com/tych0/qtile/commit/2074b9a196 and further
    #     # work in wayland
    #     # serial="CN410825SN",
    # ),
    Screen(
        bottom=statusbar(
            widgets=widgets_1,  # noqa: F405
            size=bh,
            margin=[0, ms, ms, ms],
        ),
    ),
]
