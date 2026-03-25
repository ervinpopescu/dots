from libqtile.lazy import lazy
from qtile_extras import widget

from modules.settings import colors, settings


def kbd_layout_icon():
    return widget.TextBox(
        font=settings["text_font"],
        fontsize=settings["font_size"] + 30,
        foreground=colors["darkblue"],
        mouse_callbacks={"Button1": lazy.widget["keyboardlayout"].next_keyboard()},
        padding=10,
        text="",
    )
