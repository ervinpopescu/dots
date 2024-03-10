from libqtile import bar
from libqtile.config import Screen

from modules.settings import bar_bg, settings
from modules.widgets import widgets_1, widgets_2, widgets_3

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
            widgets=widgets_1,
            size=bh,
            margin=[0, ms, ms, ms],
        ),
    ),
    Screen(
        bottom=statusbar(
            widgets=widgets_2,
            size=bh,
            margin=[0, ms, ms, ms],
        ),
    ),
    Screen(
        bottom=statusbar(
            widgets=widgets_3,
            size=bh,
            margin=[0, ms, ms, ms],
        ),
    ),
]
