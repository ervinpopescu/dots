from libqtile.lazy import lazy
from modules.settings import settings
from qtile_extras import widget
import distro

if distro.id() == "debian":
    filename = "/usr/share/pixmaps/debian-logo.png"
else:
    filename = "/usr/share/pixmaps/archlinux-logo.svg"


def os_logo():
    return widget.Image(
        filename=filename,
        margin=7,
        mouse_callbacks={"Button1": lazy.spawn(settings["cmds"]["menu"])},
    )
