from libqtile.lazy import lazy

from extras import CPUTemp
from modules.settings import cmds, text_font


def cpu_temp():
    return CPUTemp(
        font=text_font,
        fontsize=34,
        fmt="🌡️{}",
        mouse_callbacks={"Button1": lazy.spawn(cmds["htop"])},
        padding=10,
        update_interval=5,
    )
