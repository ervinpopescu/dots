import site

from qtile_extras.popup.toolkit import (
    PopupImage,
    PopupRelativeLayout,
    PopupSlider,
    PopupText,
)

from modules.settings import layout_defaults, settings
from modules.theme import colors


def music_layout():
    IMAGES_FOLDER = f"{site.getsitepackages()[0]}/qtile_extras/resources/media-icons/"
    DEFAULT_IMAGE = f"{IMAGES_FOLDER}default.png"

    return PopupRelativeLayout(
        None,
        border=colors["purple"],
        border_width=layout_defaults["border_width"],
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
