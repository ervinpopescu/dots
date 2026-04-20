from libqtile.lazy import lazy
from qtile_extras import widget

from modules.settings import settings


def mouse_over_clock():
    #     animation_step=10,
    #     font=settings.text_font,
    #     fontsize=settings.font_size,
    #     format="%H:%M",
    #     short_format="%H:%M",
    #     long_format="%d %B %Y",
    #     padding=10,
    # )
    return widget.Clock(
        font=settings.text_font,
        fontsize=settings.font_size,
        format="%H:%M",
        mouse_callbacks={"Button1": lazy.spawn("gnome-calendar")},
    )
