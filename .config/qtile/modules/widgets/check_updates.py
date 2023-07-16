from libqtile.lazy import lazy

from extras import CheckUpdates
from modules.settings import cmds, icon_font


check_updates = CheckUpdates(
    font=icon_font,
    fontsize=30,
    fmt="{}",
    mouse_callbacks={
        "Button1": lazy.spawn(cmds["update"]),
        "Button3": lazy.widget["checkupdates"].force_update(),
    },
    padding=10,
    update_interval=60,
)
