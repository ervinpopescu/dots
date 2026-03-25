from libqtile import qtile
from libqtile.config import DropDown, ScratchPad
from libqtile.core.manager import Qtile

from modules.settings import settings

qtile: Qtile


def fullscreen_dropdown_geometry():
    try:
        screen_info = qtile.core.get_output_info()
        w = min(screen_info[i].rect.width for i in range(len(screen_info)))
        h = min(screen_info[i].rect.height for i in range(len(screen_info)))
    except AttributeError:
        w, h = 1920, 1080
    ms = settings["margin_size"]
    return dict(
        width=1 - 2 * ms / w - 0.05,
        height=1 - 2 * ms / h - 0.05,
        x=ms / w + 0.025,
        y=ms / h + 0.025,
    )


def add_dpi_env_to_command(command: str):
    return " ".join(
        [
            "env",
            "QT_AUTO_SCREEN_SCALE_FACTOR=0",
            "QT_ENABLE_HIGHDPI_SCALING=0",
            "PLASMA_USE_QT_SCALING=1",
            command,
        ]
    )


scratchpad = ScratchPad(
    name="scratchpad",
    single=True,
    dropdowns=[
        DropDown(
            "term",
            settings["cmds"]["dropdown_term"],
            opacity=settings["dropdown_opacity"],
            **fullscreen_dropdown_geometry(),
            on_focus_lost_hide=False,
        ),
        DropDown(
            "keys",
            add_dpi_env_to_command("qtilekeys.py gtk"),
            opacity=settings["dropdown_opacity"],
            width=1 / 2,
            height=1 / 2,
            x=1 / 4,
            y=1 / 4,
            on_focus_lost_hide=False,
        ),
        DropDown(
            "htop",
            settings["cmds"]["htop"],
            opacity=settings["dropdown_opacity"],
            **fullscreen_dropdown_geometry(),
            on_focus_lost_hide=False,
        ),
        DropDown(
            "blueman",
            add_dpi_env_to_command(
                " ".join(settings["cmds"]["blueman"]),
            ),
            opacity=settings["dropdown_opacity"],
            width=1 / 2,
            height=1 / 2,
            x=1 / 4,
            y=1 / 4,
            on_focus_lost_hide=False,
        ),
        DropDown(
            "pavucontrol",
            add_dpi_env_to_command("pavucontrol"),
            opacity=settings["dropdown_opacity"],
            width=1 / 2,
            height=1 / 2,
            x=1 / 4,
            y=1 / 4,
            on_focus_lost_hide=False,
        ),
        DropDown(
            "files",
            add_dpi_env_to_command("nemo"),
            opacity=settings["dropdown_opacity"],
            width=4 / 5,
            height=4 / 5,
            x=1 / 10,
            y=1 / 10,
            on_focus_lost_hide=False,
        ),
        DropDown(
            "update",
            settings["cmds"]["update"],
            opacity=settings["dropdown_opacity"],
            **fullscreen_dropdown_geometry(),
            on_focus_lost_hide=False,
        ),
        DropDown(
            "spotify",
            "spotify",
            opacity=settings["dropdown_opacity"],
            width=1 / 2,
            height=1 / 2,
            x=1 / 4,
            y=1 / 4,
            on_focus_lost_hide=False,
        ),
    ],
)
