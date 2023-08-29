from libqtile.lazy import lazy

from extras.widgets import Battery
from modules.settings import colors, settings

battery = Battery(
    font=settings["text_font"],
    fontsize=settings["font_size"],
    foreground=colors["fg2"],
    mouse_callbacks={"Button1": lazy.group["scratchpad"].dropdown_toggle("htop")},
    padding=5,
)
