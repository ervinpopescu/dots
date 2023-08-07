from libqtile.lazy import lazy
from qtile_extras import widget

from modules.settings import colors, icon_font


powermenu = widget.TextBox(
    font=icon_font,
    fontsize=30,
    foreground=colors["yellow"],
    mouse_callbacks={"Button1": lazy.spawn("nwgbar")},
    padding=10,
    text="",
)
