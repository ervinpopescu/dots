from libqtile import qtile
from libqtile.config import DropDown, ScratchPad
from libqtile.core.manager import Qtile

from modules.settings import settings

qtile: Qtile
screen_info = qtile.core.get_screen_info()
screen_width = min([screen_info[i].width for i in range(len(screen_info))])
screen_height = min([screen_info[i].height for i in range(len(screen_info))])
scratchpad = ScratchPad(
    name="scratchpad",
    single=True,
    dropdowns=[
        DropDown(
            "term",
            settings["cmds"]["dropdown_term"],
            opacity=settings["dropdown_opacity"],
            width=1 - 2 * settings["margin_size"] / screen_width - 0.05,
            height=1 - 2 * settings["margin_size"] / screen_height - 0.05,
            x=settings["margin_size"] / screen_width + 0.025,
            y=settings["margin_size"] / screen_height + 0.025,
            on_focus_lost_hide=False,
        ),
        DropDown(
            "keys",
            "qtilekeys.py gtk",
            opacity=settings["dropdown_opacity"],
            width=1384 / screen_width,
            height=0.8,
            x=(1 - 1384 / screen_width) / 2,
            y=0.1,
            on_focus_lost_hide=False,
        ),
        DropDown(
            "htop",
            settings["cmds"]["htop"],
            opacity=settings["dropdown_opacity"],
            width=1 - 2 * settings["margin_size"] / screen_width - 0.05,
            height=1 - 2 * settings["margin_size"] / screen_height - 0.05,
            x=settings["margin_size"] / screen_width + 0.025,
            y=settings["margin_size"] / screen_height + 0.025,
            on_focus_lost_hide=False,
        ),
        DropDown(
            "blueman",
            settings["cmds"]["blueman"],
            opacity=settings["dropdown_opacity"],
            width=1 / 2,
            height=1 / 2,
            x=1 / 4,
            y=1 / 4,
            on_focus_lost_hide=False,
        ),
        DropDown(
            "pavucontrol",
            "pavucontrol",
            opacity=settings["dropdown_opacity"],
            width=1 / 2,
            height=1 / 2,
            x=1 / 4,
            y=1 / 4,
            on_focus_lost_hide=False,
        ),
        DropDown(
            "files",
            "nemo",
            # opacity=settings["dropdown_opacity"],
            opacity=1,
            width=4 / 5,
            height=4 / 5,
            x=1 / 10,
            y=1 / 10,
            on_focus_lost_hide=False,
        ),
    ],
)
