import pprint

from libqtile.log_utils import logger
from qtile_extras import widget

from extras import Battery, MouseOverClock, WidgetBox
from modules.decorations import decorations
from modules.settings import colors, icon_font, margin_size

from .arch_logo import arch_logo
from .battery import battery
from .check_updates import check_updates
from .cpu_temp import cpu_temp
from .current_layout_icon import current_layout_icon
from .data import data
from .github_notif import github_notif
from .group_box import group_box
from .kbd_layout import kbd_layout
from .kbd_layout_icon import kbd_layout_icon

# from .maximize import maximize
from .mouse_over_clock import mouse_over_clock
from .music import music
from .powermenu import powermenu
from .systray import systray
from .task_list import task_list
from .wallpaper import wallpaper
from .weather import weather

ms = margin_size // 4
decor = decorations["single_decor"]
group_decor = decorations["group_single_decor"]


def small_spacer():
    return widget.Spacer(length=ms)


def stretch_spacer():
    return widget.Spacer()


def pipe():
    return widget.Sep(
        foreground="#ddb6dc",
        padding=5,
        linewidth=2,
        size_percent=100,
    )


def slash_left():
    return widget.TextBox(
        "/",
        font=icon_font,
        fontsize=65,
        foreground="#ddb6dc",
        padding=0,
    )


def slash_right():
    return widget.TextBox(
        "\\",
        font=icon_font,
        fontsize=65,
        foreground="#ddb6dc",
        padding=0,
    )


# widget_box_1 = WidgetBox(
#     fontsize=40,
#     foreground=colors["darkblue"],
#     padding=10,
#     # start_opened=True,
#     text_closed="",
#     text_open="",
#     widgets=[
#         small_spacer(),
#         check_updates(),
#         small_spacer(),
#         data(),
#     ],
# )

# widget_box_2 = WidgetBox(
#     fontsize=40,
#     close_button_location="right",
#     foreground=colors["darkblue"],
#     padding=10,
#     # start_opened=True,
#     text_closed="",
#     text_open="",
#     widgets=[
#         small_spacer(),
#         weather(),
#         small_spacer(),
#         cpu_temp(),
#         small_spacer(),
#         kbd_layout(),
#         kbd_layout_icon(),
#         small_spacer(),
#     ],
# )


# for w in widget_box_1.widgets:
#     if not isinstance(w, (widget.Spacer, widget.TextBox, widget.KeyboardLayout)):
#         w.decorations = decor["decorations"]
#     if isinstance(w, (widget.TextBox, widget.KeyboardLayout)):
#         w.decorations = group_decor["decorations"]

# for w in widget_box_2.widgets:
#     if not isinstance(w, (widget.Spacer, widget.TextBox, widget.KeyboardLayout)):
#         w.decorations = decor["decorations"]
#     if isinstance(w, (widget.TextBox, widget.KeyboardLayout)):
#         w.decorations = group_decor["decorations"]

first_stretch_spacer = stretch_spacer()
second_stretch_spacer = stretch_spacer()
# logger.info()

widgets_1 = [
    arch_logo(),
    # small_spacer(),
    # music(),
    small_spacer(),
    check_updates(),
    small_spacer(),
    data(),
    # small_spacer(),
    # widget_box_1,
    small_spacer(),
    group_box(),
    small_spacer(),
    current_layout_icon(),
    small_spacer(),
    task_list(),
    first_stretch_spacer,
    systray(),
    second_stretch_spacer,
    # widget_box_2,
    small_spacer(),
    weather(),
    small_spacer(),
    cpu_temp(),
    small_spacer(),
    kbd_layout(),
    kbd_layout_icon(),
    small_spacer(),
    github_notif(),
    small_spacer(),
    battery(),
    # small_spacer(),
    # widget.BatteryIcon(
    #     foreground=colors["darkblue"],
    #     padding=1,
    #     scale=1.4,
    #     theme_path="/home/ervin/.config/qtile-x11/battery-icons/",
    #     usemask=True,
    #     update_interval=1,
    # ),
    small_spacer(),
    mouse_over_clock(),
    small_spacer(),
    wallpaper(),
    small_spacer(),
    powermenu(),
]

ss1_index = widgets_1.index(first_stretch_spacer)
ss2_index = widgets_1.index(second_stretch_spacer)


for w in widgets_1:
    if not isinstance(w, (widget.Systray, widget.Spacer, Battery, widget.BatteryIcon)):
        w.decorations = decor["decorations"]

    if isinstance(w, (Battery, widget.BatteryIcon, widget.TextBox, widget.KeyboardLayout)):
        w.decorations = group_decor["decorations"]

widgets_2 = [
    w
    for w in widgets_1[:ss1_index] + widgets_1[ss2_index:]
    if not isinstance(w, widget.Systray)
]
# side_widgets = []


__all__ = [
    "widgets_1",
    "widgets_2",
]
