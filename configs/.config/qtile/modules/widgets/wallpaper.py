from libqtile.lazy import lazy
from qtile_extras import widget

from modules.settings import colors, settings


def wallpaper():
    return widget.TextBox(
        font=settings["icon_font"],
        foreground=colors["red"],
        mouse_callbacks={
            "Button1": lazy.spawn("/home/ervin/bin/change_wallpaper.sh rand")
        },
        padding=10,
        text="",
    )
    # return widget.Wallpaper(
    #     directory="~/Pictures/wallpapers/rand/",
    #     font="Font Awesome 6 Free Solid",
    #     fontsize=34,
    #     foreground=colors["red"],
    #     label="",
    #     padding=10,
    #     random_selection=True,
    #     wallpaper=os.path.expanduser("~/Pictures/wallpapers/rand/windowsy.png"),
    # )
