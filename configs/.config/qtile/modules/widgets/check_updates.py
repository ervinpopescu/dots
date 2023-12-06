from libqtile.lazy import lazy

from extras.widgets import CheckUpdates
from modules.settings import settings


def check_updates():
    return CheckUpdates(
        font=settings["icon_font"],
        fontsize=settings["font_size"],
        fmt="{}",
        mouse_callbacks={
            "Button1": lazy.spawn(settings["cmds"]["update"]),
            "Button3": lazy.widget["checkupdates"].force_update(),
        },
        padding=10,
        update_interval=60,
    )
