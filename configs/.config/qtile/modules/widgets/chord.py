from qtile_extras import widget

from modules.settings import colors, settings


def chord():
    return widget.Chord(
        font=settings["text_font"],
        fontsize=settings["font_size"],
        foreground=colors["darkblue"],
        fmt="chord {}",
        padding=10,
    )
