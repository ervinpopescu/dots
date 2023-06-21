from libqtile.lazy import lazy

from extras import MouseOverClock
from modules.settings import colors, text_font


def mouse_over_clock():
    return MouseOverClock(
        font=text_font,
        fontsize=34,
        foreground=colors["darkblue"],
        format="%H:%M",
        long_format="%H:%M:%S",
        # long_format="%H:%M:%S %d/%m/%y",
        mouse_callbacks={"Button1": lazy.spawn("gsimplecal")},
        padding=10,
    )
