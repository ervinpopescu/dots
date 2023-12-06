import subprocess

from libqtile.lazy import lazy
from qtile_extras.popup.toolkit import (
    PopupAbsoluteLayout,
    PopupImage,
    PopupRelativeLayout,
    PopupSlider,
    PopupText,
)

from modules.functions import location
from modules.settings import settings
from modules.theme import colors


@lazy.function
def weather_popup(qtile):
    wttr = (
        subprocess.check_output(
            [
                "/home/ervin/bin/wttr.sh",
                location(),
                "?M?T?0",
            ]
        )
        .decode("utf-8")
        .splitlines()
    )
    wttr.pop(0)
    wttr.pop(0)
    wttr = "\n".join(wttr)
    controls = [
        PopupText(
            font=settings["text_font"],
            pos_x=10,
            pos_y=10,
            fontsize=25,
            foreground="000000",
            text=wttr,
            width=500,
            height=300,
        )
    ]
    layout = PopupAbsoluteLayout(
        qtile,
        width=500,
        height=300,
        controls=controls,
        opacity=0.96,
        background=qtile.widgets_map["weather"].foreground,
        initial_focus=None,
    )
    layout.show(
        x=2880 - layout.width - settings["margin_size"],
        y=qtile.current_screen.top.info()["size"] + settings["margin_size"],
        warp_pointer=True,
    )


def music_layout():
    IMAGES_FOLDER = "/usr/lib/python3.10/site-packages/qtile_extras/resources/media-icons/"
    DEFAULT_IMAGE = f"{IMAGES_FOLDER}default.png"

    return PopupRelativeLayout(
        None,
        border=colors["purple"],
        border_width=settings["layout_defaults"]["border_width"],
        background=colors["bg0"],
        width=1440,
        height=400,
        controls=[
            PopupText(
                "",
                name="title",
                font=settings["text_font"],
                fontsize=25,
                pos_x=0.3,
                pos_y=0.1,
                width=0.65,
                height=0.14,
                h_align="left",
                v_align="top",
            ),
            PopupText(
                "",
                name="artist",
                font=settings["text_font"],
                fontsize=25,
                pos_x=0.3,
                pos_y=0.24,
                width=0.65,
                height=0.14,
                h_align="left",
                v_align="middle",
            ),
            PopupText(
                "",
                name="album",
                font=settings["text_font"],
                fontsize=25,
                pos_x=0.3,
                pos_y=0.38,
                width=0.65,
                height=0.14,
                h_align="left",
                v_align="bottom",
            ),
            PopupImage(
                name="artwork",
                filename=DEFAULT_IMAGE,
                pos_x=0.05,
                pos_y=0.1,
                width=0.21,
                height=0.42,
            ),
            PopupSlider(
                name="progress",
                bar_size=10,
                pos_x=0.05,
                pos_y=0.6,
                width=0.9,
                height=0.1,
                marker_size=0,
            ),
            PopupImage(
                name="previous",
                filename=f"{IMAGES_FOLDER}previous.svg",
                highlight=colors["bg1"],
                mask=True,
                pos_y=0.8,
                pos_x=0.125,
                width=0.15,
                height=0.1,
            ),
            PopupImage(
                name="play_pause",
                filename=f"{IMAGES_FOLDER}play_pause.svg",
                highlight=colors["bg1"],
                mask=True,
                pos_y=0.8,
                pos_x=0.325,
                width=0.15,
                height=0.1,
            ),
            PopupImage(
                name="stop",
                filename=f"{IMAGES_FOLDER}stop.svg",
                highlight=colors["bg1"],
                mask=True,
                pos_y=0.8,
                pos_x=0.525,
                width=0.15,
                height=0.1,
            ),
            PopupImage(
                name="next",
                filename=f"{IMAGES_FOLDER}next.svg",
                highlight=colors["bg1"],
                mask=True,
                pos_y=0.8,
                pos_x=0.725,
                width=0.15,
                height=0.1,
            ),
        ],
        close_on_click=False,
        hide_on_mouse_leave=True,
    )
