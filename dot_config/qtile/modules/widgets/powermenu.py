from libqtile import widget
from libqtile.lazy import lazy

from modules.settings import colors, settings


def powermenu():
    return widget.TextBox(
        "",
        background=colors["darkblue"],
        font=settings.icon_font,
        fontsize=settings.font_size,
        foreground=colors["red"],
        mouse_callbacks={"Button1": lazy.spawn(settings.cmds.nwgbar)},
        padding=10,
    )
