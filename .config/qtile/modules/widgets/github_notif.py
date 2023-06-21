from libqtile.lazy import lazy

from modules.path import qtile_path
from modules.settings import bar_height, colors
from qtile_extras import widget


def github_notif():
    return widget.GithubNotifications(
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
        token_file=qtile_path + "/github_token",
    )
