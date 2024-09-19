from libqtile.lazy import lazy

from extras.widgets import MouseOverClock
from modules.settings import colors, settings


def mouse_over_clock():
    return MouseOverClock(
        font=settings["text_font"],
        fontsize=settings["font_size"],
        foreground=colors["darkblue"],
        format="%H:%M",
        # long_format="%H:%M:%S",
        long_format="%a %d/%m/%y %H:%M:%S",
        mouse_callbacks={"Button1": lazy.spawn("gsimplecal")},
        padding=10,
        name="mouse_over_clock",
    )
