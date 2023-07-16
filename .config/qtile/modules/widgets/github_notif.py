from libqtile.lazy import lazy
from qtile_extras import widget

from modules.path import config_path
from modules.settings import bar_height, colors

github_notif = widget.GithubNotifications(
    active_colour=colors["red"],
    icon_size=bar_height - 15,
    inactive_colour=colors["darkblue"],
    mouse_callbacks={
        "Button1": lazy.spawn(
            ["xdg-open", "https://github.com/notifications"],
        ),
        "Button3": lazy.widget["githubnotifications"].eval("self.update()"),
    },
    padding=10,
    token_file=f"{config_path}/github_token",
)
