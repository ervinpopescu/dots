from libqtile.lazy import lazy

from extras.widgets import Battery
from modules.settings import cmds, colors, text_font


battery = Battery(
    font=text_font,
    fontsize=34,
    foreground=colors["fg2"],
    mouse_callbacks={"Button1": lazy.group["scratchpad"].dropdown_toggle("htop")},
    padding=5,
)
