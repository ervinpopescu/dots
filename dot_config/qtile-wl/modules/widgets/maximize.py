from qtile_extras import widget

from modules.functions import set_layout_all
from modules.settings import colors, settings


def maximize():
    return widget.TextBox(
        font=settings["icon_font"],
        fontsize=settings["font_size"],
        foreground=colors["darkblue"],
        mouse_callbacks={"Button1": set_layout_all()},
        padding=15,
        text="",
    )
