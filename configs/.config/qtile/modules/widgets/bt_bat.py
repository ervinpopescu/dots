from extras.widgets import BtBattery

from libqtile.lazy import lazy
from modules.settings import colors, settings


def bt_bat():
    return BtBattery(
        name="bt_battery",
        font=settings["text_font"],
        fontsize=settings["font_size"] + 4,
        foreground=colors["fg2"],
        mouse_callbacks={"Button1": lazy.spawn("blueman-manager")},
        padding=5,
    )
