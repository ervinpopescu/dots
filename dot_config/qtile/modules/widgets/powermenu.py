from libqtile.lazy import lazy
from qtile_extras import widget

from modules.settings import colors, settings


def powermenu():
    return widget.TextBox(
        name="powermenu",
        font=settings["icon_font"],
        fontsize=30,
        foreground=colors["yellow"],
        mouse_callbacks={"Button1": lazy.spawn("nwgbar")},
        padding=10,
        text="",
    )
