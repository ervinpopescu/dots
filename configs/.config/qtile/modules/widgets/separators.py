from modules.settings import colors, icon_font, margin_size
from qtile_extras import widget

from modules.settings import colors, settings


def small_spacer(**config):
    return widget.Spacer(**config)


def stretch_spacer():
    return widget.Spacer()


def pipe(**config):
    return widget.Sep(
        padding=10,
        linewidth=5,
        size_percent=100,
        **config,
    )


def slash_left(**config):
    return widget.TextBox("/", font=settings["icon_font"], fontsize=65, padding=5, **config)


def slash_right(**config):
    return widget.TextBox(
        "\\",
        font=settings["icon_font"],
        fontsize=65,
        padding=5,
        **config,
    )
