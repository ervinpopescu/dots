from libqtile.widget.base import _Widget
from qtile_extras import widget

from extras.widgets import Battery, BtBattery, TaskList, WidgetBox
from modules.decorations import decorations
from modules.settings import colors, settings

# Local imports
from modules.widgets.battery import battery
from modules.widgets.battery_icon import battery_icon
from modules.widgets.bt_bat import bt_bat
from modules.widgets.chord import chord
from modules.widgets.current_layout_icon import current_layout_icon
from modules.widgets.github_notif import github_notif
from modules.widgets.group_box import group_box
from modules.widgets.mouse_over_clock import mouse_over_clock
from modules.widgets.os_logo import os_logo
from modules.widgets.powermenu import powermenu
from modules.widgets.separators import pipe, small_spacer, stretch_spacer
from modules.widgets.systray import systray
from modules.widgets.task_list import task_list
from modules.widgets.touchpad import touchpad
from modules.widgets.wallpaper import wallpaper
from modules.widgets.widgetbox import widget_box_1, widget_box_2

# Constants
MARGIN_SIZE = settings["margin_size"] // 2 - 2
SINGLE_DECORATION = decorations["single_decor"]
GROUP_DECORATION = decorations["group_single_decor"]

# Create a list of widgets for the first screen
widgets_1: list[_Widget] = [
    os_logo(),
    widget_box_1,
    group_box(),
    current_layout_icon(),
    task_list(),
    systray(),
    widget_box_2,
    github_notif(),
    # touchpad(),
    chord(),
    battery(),
    battery_icon(),
    bt_bat(),
    mouse_over_clock(),
    wallpaper(),
    powermenu(),
]

# Customize decorations for certain widgets
for w in widgets_1:
    if not isinstance(
        w, (Battery, widget.BatteryIcon, widget.Spacer, widget.Systray, widget.TaskList)
    ):
        w.decorations = SINGLE_DECORATION["decorations"]

    if isinstance(
        w, (Battery, BtBattery, widget.BatteryIcon, widget.KeyboardLayout, widget.TextBox)
    ):
        w.decorations = GROUP_DECORATION["decorations"]

# Duplicate widgets_1 into widgets_2 with specific conditions
widgets_2 = []
widgets_3 = []
sm_spacer = small_spacer(length=MARGIN_SIZE)
st_spacer = stretch_spacer()
for w in widgets_1:
    if not isinstance(
        w, (widget.Systray, WidgetBox, widget.GithubNotifications, widget.GroupBox, TaskList)
    ):
        widgets_2.append(w)
        widgets_3.append(w)
    elif isinstance(w, widget.GroupBox):
        gb = group_box()
        gb.decorations = SINGLE_DECORATION["decorations"]
        widgets_2.append(gb)
        gb = group_box()
        gb.decorations = SINGLE_DECORATION["decorations"]
        widgets_3.append(gb)
    elif isinstance(w, TaskList):
        tl = task_list()
        tl.decorations = SINGLE_DECORATION["decorations"]
        widgets_2.append(tl)
        tl = task_list()
        tl.decorations = SINGLE_DECORATION["decorations"]
        widgets_3.append(tl)

# Insert Spacer widgets into widgets_1
i = 1
while i < len(widgets_1):
    w = widgets_1[i]
    match w.name:
        case "systray":
            widgets_1.insert(i, st_spacer)
            i += 2
        case "second_widgetbox":
            widgets_1.insert(i, st_spacer)
            i += 2
        case "battery":
            widgets_1.insert(i, sm_spacer)
            i += 2
        case "battery_icon":
            i += 1
        case "bt_battery":
            ins = pipe(
                name="battery_sep",
                foreground=colors["bg2"],
            )
            ins.decorations = GROUP_DECORATION["decorations"]
            widgets_1.insert(i, ins)
            i += 2
        case "powermenu":
            break
        case _:
            widgets_1.insert(i, sm_spacer)
            i += 2

# Insert Spacer widgets into widgets_2
i = 1
while i < len(widgets_2):
    w = widgets_2[i]
    match w.name:
        case "battery":
            widgets_2.insert(i, st_spacer)
            i += 2
        case "battery_icon":
            i += 1
        case "bt_battery":
            widgets_2.insert(i, next(item for item in widgets_1 if item.name == "battery_sep"))
            i += 2
        case "powermenu":
            break
        case _:
            widgets_2.insert(i, sm_spacer)
            i += 2

# Insert Spacer widgets into widgets_2
i = 1
while i < len(widgets_3):
    w = widgets_3[i]
    match w.name:
        case "battery":
            widgets_3.insert(i, st_spacer)
            i += 2
        case "battery_icon":
            i += 1
        case "bt_battery":
            widgets_3.insert(i, next(item for item in widgets_1 if item.name == "battery_sep"))
            i += 2
        case "powermenu":
            break
        case _:
            widgets_3.insert(i, sm_spacer)
            i += 2

# Define public exports
__all__ = ["widgets_1", "widgets_2", "widgets_3"]
