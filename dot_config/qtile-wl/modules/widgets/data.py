from libqtile.lazy import lazy

from extras import Uptime
from modules.settings import settings


def uptime():
    return Uptime(
        font=settings["text_font"],
        fontsize=settings["font_size"],
        mouse_callbacks={
            "Button1": lazy.group["scratchpad"].dropdown_toggle("htop"),
        },
        padding=10,
        update_interval=3600,
    )
