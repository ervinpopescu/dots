from extras.widgets import Systray
from modules.decorations import decorations
from modules.settings import colors, settings


def systray():
    return Systray(
        highlight_colour=colors["bg1"],
        icon_size=24,
        icon_theme="Papirus-Dark",
        menu_background=colors["bg0"],
        menu_font=settings.text_font,
        menu_fontsize=15,
        menu_icon_size=15,
        menu_width=500,
        opacity=0.95,
        padding=10,
        **decorations["systray_decor"],  # type: ignore
    )
