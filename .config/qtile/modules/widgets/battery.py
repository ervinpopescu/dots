from libqtile.lazy import lazy

from extras import Battery
from modules.settings import cmds, colors, text_font


def battery():
    return Battery(
        font=text_font,
        fontsize=34,
        foreground=colors["fg2"],
        mouse_callbacks={"Button1": lazy.spawn(cmds["htop"])},
        padding=10,
    )
