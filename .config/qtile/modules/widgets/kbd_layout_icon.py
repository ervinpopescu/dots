from libqtile.lazy import lazy
from qtile_extras import widget

from modules.settings import colors, icon_font


def kbd_layout_icon():
    return widget.TextBox(
        font=icon_font,
        fontsize=30,
        foreground=colors["darkblue"],
        mouse_callbacks={"Button1": lazy.widget["keyboardlayout"].next_keyboard()},
        padding=10,
        text="",
    )
