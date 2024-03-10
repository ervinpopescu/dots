from libqtile.lazy import lazy
from qtile_extras import widget

# import os
# import subprocess
from modules.settings import colors, settings


def wallpaper():
    return widget.TextBox(
        font=settings["icon_font"],
        foreground=colors["red"],
        mouse_callbacks={"Button1": lazy.spawn("/home/ervin/bin/run_wall.sh rand all")},
        padding=10,
        text="",
    )
    # pix = subprocess.check_output("xdg-user-dir PICTURES".split()).decode()
    # return widget.Wallpaper(
    #     # random_selection=True,
    #     # directory=os.path.join(
    #     #     pix,
    #     #     "wallpapers",
    #     #     "rand",
    #     # ),
    #     font="Font Awesome 6 Free Solid",
    #     fontsize=34,
    #     foreground=colors["red"],
    #     label="",
    #     padding=10,
    #     wallpaper=os.path.join(
    #         pix,
    #         "wallpapers",
    #         "rand",
    #         "windowsy.png",
    #     ),
    # )
