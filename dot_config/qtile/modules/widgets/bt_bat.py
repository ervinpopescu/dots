from extras.widgets import BtBattery
from modules.settings import colors, settings


def bt_bat():
    return BtBattery(
        font=settings.text_font,
        fontsize=settings.font_size + 4,
        foreground=colors["darkblue"],
        format="{percentage:0.0f}%",
        update_interval=10,
    )
