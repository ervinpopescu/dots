from qtile_extras import widget

from modules.functions import set_layout_all
from modules.settings import colors, icon_font


def maximize():
    return widget.TextBox(
        font=icon_font,
        fontsize=40,
        foreground=colors["darkblue"],
        mouse_callbacks={"Button1": set_layout_all()},
        padding=15,
        text="",
    )
