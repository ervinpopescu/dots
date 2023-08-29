from libqtile.lazy import lazy

from extras.widgets import BtBattery
from modules.settings import colors, settings

bt_bat = BtBattery(
    font=settings["text_font"],
    fontsize=settings["font_size"] + 4,
    foreground=colors["fg2"],
    mouse_callbacks={"Button1": lazy.spawn("blueman-manager")},
    padding=5,
)
