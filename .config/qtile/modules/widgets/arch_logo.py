from libqtile.lazy import lazy

from modules.settings import cmds
from qtile_extras import widget


def arch_logo():
    return widget.Image(
        filename="/usr/share/pixmaps/archlinux-logo.svg",
        margin=7,
        mouse_callbacks={"Button1": lazy.spawn(cmds["menu"])},
    )
