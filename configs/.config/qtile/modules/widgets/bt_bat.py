from libqtile.lazy import lazy

from extras.widgets import BtBattery
from modules.settings import colors, text_font

bt_bat = BtBattery(
    font=text_font,
    fontsize=34,
    foreground=colors["fg2"],
    mouse_callbacks={"Button1": lazy.spawn("blueman-manager")},
    padding=5,
)
