from qtile_extras import widget

from modules.settings import colors, settings

ms = settings["margin_size"] // 4


def small_spacer():
    return widget.Spacer(length=ms)


def stretch_spacer():
    return widget.Spacer()


def pipe():
    return widget.Sep(
        foreground=colors["purple"],
        padding=5,
        linewidth=2,
        size_percent=100,
    )


def slash_left():
    return widget.TextBox(
        "/",
        font=settings["icon_font"],
        fontsize=65,
        foreground=colors["purple"],
        padding=0,
    )


def slash_right():
    return widget.TextBox(
        "\\",
        font=settings["icon_font"],
        fontsize=65,
        foreground=colors["purple"],
        padding=0,
    )
