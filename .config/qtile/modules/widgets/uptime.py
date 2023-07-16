from libqtile.lazy import lazy

from extras import Uptime
from modules.settings import cmds, text_font


uptime = Uptime(
    font=text_font,
    fontsize=34,
    mouse_callbacks={
        "Button1": lazy.group["scratchpad"].dropdown_toggle("htop"),
    },
    padding=10,
    update_interval=3600,
)
