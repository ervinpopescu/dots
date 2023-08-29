from libqtile import bar
from libqtile.config import Screen

from modules.settings import settings, bar_bg
from modules.widgets import widgets_1, widgets_2

bh = settings["bar_height"]
ms = settings["margin_size"]


def statusbar(widgets, margin, size):
    return bar.Bar(
        widgets,
        size=size,
        margin=margin,
        background=bar_bg,
        # fake_transparency=True,
    )


screens = [
    Screen(
        top=statusbar(
            widgets=widgets_1,
            size=bh,
            margin=[ms, ms, 0, ms],
        ),
    ),
    Screen(
        top=statusbar(
            widgets=widgets_2,
            size=bh,
            margin=[ms, ms, 0, ms],
        ),
    ),
]
