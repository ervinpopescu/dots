from libqtile.lazy import lazy

from modules.popups.music_popup import music_popup
from modules.settings import colors, settings
from qtile_extras import widget


def music():
    return widget.Mpris2(
        display_metadata=["xesam:title", "xesam:artist"],
        font=settings.text_font,
        max_chars=30,
        mouse_callbacks={
            "Button1": lazy.window.function(
                music_popup(
                    width=1 / 4,
                    height=1 / 3,
                    x=settings.margin_size,
                    y=settings.bar_height + 2 * settings.margin_size,
                )
            )
        },
    )
