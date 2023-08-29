from libqtile.lazy import lazy
from modules.settings import settings
from qtile_extras import widget

os_logo = widget.Image(
    filename="/usr/share/pixmaps/debian-logo.png",
    margin=7,
    mouse_callbacks={"Button1": lazy.spawn(settings["cmds"]["menu"])},
)
