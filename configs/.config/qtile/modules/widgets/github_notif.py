from libqtile.lazy import lazy
from modules.settings import colors, config_path, settings
from qtile_extras.widget import GithubNotifications


def github_notif():
    return GithubNotifications(
        active_colour=colors["red"],
        icon_size=settings["bar_height"] - 15,
        inactive_colour=colors["darkblue"],
        mouse_callbacks={
            "Button1": lazy.spawn(
                ["xdg-open", "https://github.com/notifications"],
            ),
            "Button3": lazy.widget["githubnotifications"].update(),
        },
        padding=10,
        token_file=f"{config_path}/github_token",
    )
