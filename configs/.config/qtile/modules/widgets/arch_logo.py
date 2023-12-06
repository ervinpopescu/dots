
from libqtile.lazy import lazy
from qtile_extras import widget

from modules.settings import settings

arch_logo = widget.Image(
    filename="/usr/share/pixmaps/archlinux-logo.svg",
    margin=7,
    mouse_callbacks={"Button1": lazy.spawn(settings["cmds"]["menu"])},
)
