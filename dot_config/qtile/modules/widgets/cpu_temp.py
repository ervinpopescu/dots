from libqtile.lazy import lazy

from extras.widgets import CPUTemp
from modules.settings import settings


def cpu_temp():
    return CPUTemp(
        font=settings["text_font"],
        fontsize=settings["font_size"],
        fmt="🌡️{}",
        mouse_callbacks={"Button1": lazy.group["scratchpad"].dropdown_toggle("htop")},
        padding=10,
        update_interval=5,
    )
