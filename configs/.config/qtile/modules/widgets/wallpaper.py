from libqtile.lazy import lazy
from modules.settings import colors, settings
from qtile_extras import widget

from modules.settings import colors, settings


def wallpaper():
    return widget.Wallpaper(
        directory="/usr/share/backgrounds/gnome",
        # directory="~/Pictures/wallpapers/rand/",
        font="Font Awesome 6 Free Solid",
        fontsize=settings["font_size"],
        foreground=colors["red"],
        label="",
        padding=10,
        random_selection=True,
        # wallpaper=os.path.expanduser("~/Pictures/wallpapers/rand/windowsy.png"),
    )
    # return widget.TextBox(
    #     font=icon_font,
    #     foreground=colors["red"],
    #     mouse_callbacks={"Button1": lazy.spawn("/home/ervin/bin/change_wallpaper.sh rand")},
    #     padding=10,
    #     text="",
    # )
