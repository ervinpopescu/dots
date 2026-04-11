from libqtile import widget

from modules.settings import colors, settings


def maximize():
    return widget.TextBox(
        "",
        background=colors["darkblue"],
        font=settings.icon_font,
        fontsize=settings.font_size,
        foreground=colors["red"],
    )
