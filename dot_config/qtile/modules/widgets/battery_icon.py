from libqtile import widget

from modules.path import config_path
from modules.settings import colors


def battery_icon():
    return widget.BatteryIcon(
        foreground=colors["darkblue"],
        scale=1.6,
        theme_path=f"{config_path}/battery-icons/",
        usemask=True,
        update_interval=1,
    )
