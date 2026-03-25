from libqtile import bar
from libqtile.config import Screen

from modules.settings import bar_bg, settings
from modules.widgets import widgets_1, widgets_2

bh = settings["bar_height"]
ms = settings["margin_size"]


def statusbar(widgets, margin, size):
    return bar.Bar(
        widgets,
        size=size,
        margin=margin,
        background=bar_bg,
    )


screens = [
    Screen(
        bottom=statusbar(
            widgets=widgets_1,  # noqa: F405
            size=bh,
            margin=[0, ms, ms, ms],
        ),
    ),
    Screen(
        bottom=statusbar(
            widgets=widgets_2,  # noqa: F405
            size=bh * 2 // 3,
            margin=[
                0,
                ms - 5,
                ms - 5,
                ms - 5,
            ],
        ),
        # needs https://github.com/tych0/qtile/commit/2074b9a196 and further
        # work in wayland
        # serial="CN41010NQC",
    ),
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
]
