from libqtile.lazy import lazy
from qtile_extras import widget

from modules.path import config_path
from modules.settings import colors, settings


def github_notif():
    return widget.GithubNotifications(
        active_colour=colors["red"],
        icon_size=settings["bar_height"] - 15,
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
