from libqtile.lazy import lazy
from qtile_extras import widget

from modules.popups import music_layout
from modules.settings import colors, settings


def music():
    return widget.Mpris2(
        font=settings["text_font"],
        foreground=colors["darkblue"],
        format="{xesam:title} - {xesam:artist}",
        mouse_callbacks={
            "Button1": lazy.widget["mpris2"].show_popup(),
            "Button3": lazy.widget["mpris2"].force_update(),
        },
        popup_layout=music_layout(),
        popup_show_args={
            "relative_to": 1,
            "x": settings["margin_size"],
            "y": settings["bar_height"] + 2 * settings["margin_size"],
            # "centered": True,
            "warp_pointer": True,
        },
        scroll_delay=10,
        scroll_interval=0.01,
        scroll=True,
        width=300,
    )
