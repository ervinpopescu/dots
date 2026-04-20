from typing import TYPE_CHECKING, Any, Protocol, cast

from extras.widgets import Battery, BtBattery, TaskList, WidgetBox  # noqa: F401
from libqtile.widget.base import _Widget
from modules.decorations import decorations
from modules.settings import colors

# Local imports
# from modules.widgets.battery import battery
# from modules.widgets.battery_icon import battery_icon
# from modules.widgets.bt_bat import bt_bat
# from modules.widgets.check_updates import check_updates
# from modules.widgets.chord import chord
# from modules.widgets.cpu_temp import cpu_temp
from modules.widgets.current_layout_icon import current_layout_icon
from modules.widgets.github_notif import github_notif
from modules.widgets.group_box import group_box

# from modules.widgets.kbd_layout import kbd_layout
# from modules.widgets.kbd_layout_icon import kbd_layout_icon
from modules.widgets.mouse_over_clock import mouse_over_clock

# from modules.widgets.music import music
from modules.widgets.os_logo import os_logo
from modules.widgets.powermenu import powermenu
from modules.widgets.separators import pipe, small_spacer, stretch_spacer
from modules.widgets.systray import systray
from modules.widgets.task_list import task_list  # noqa: F401

# from modules.widgets.touchpad import touchpad
from modules.widgets.wallpaper import wallpaper

# from modules.widgets.weather import weather
from modules.widgets.widgetbox import widget_box_1, widget_box_2  # noqa: F401
from qtile_extras import widget

if TYPE_CHECKING:

    class HasDecorations(Protocol):
        decorations: Any


# Constants
MARGIN_SIZE = 10 // 2 - 2
SINGLE_DECORATION = decorations["single_decor"]
GROUP_DECORATION = decorations["group_single_decor"]
icon_size = 36 - 12
margin_y = icon_size + 4
margin_x = margin_y - icon_size
padding_x = (margin_y - icon_size) // 2
padding_y = 0
# margin_y = 0
# margin_x = 5
# padding_x = 0

# Create a list of widgets for the first screen
widgets_1: list[_Widget] = [
    os_logo(),
    # widget_box_1,
    group_box(),
    current_layout_icon(),
    widget.TaskList(
        border=colors["darkblue"],
        highlight_method="block",
        icon_only=False,
        rounded=False,
        theme_mode="preferred",
        theme_path="/usr/share/icons/Papirus",
        icon_size=icon_size + 5,
        margin_y=margin_y - 25,
        txt_floating="",
        txt_maximized="",
        txt_minimized="",
        font="CaskaydiaCove Nerd Font Mono Bold",
    ),
    systray(),
    # widget_box_2,
    github_notif(),
    mouse_over_clock(),
    wallpaper(),
    powermenu(),
]

# Apply decorations to widgets
for w in widgets_1:
    if not isinstance(
        w, (Battery, widget.BatteryIcon, widget.Spacer, widget.Systray, widget.TaskList)
    ):
        if hasattr(w, "decorations"):
            casted_w = cast("HasDecorations", w)
            casted_w.decorations = SINGLE_DECORATION["decorations"]

    if isinstance(
        w,
        (Battery, BtBattery, widget.BatteryIcon, widget.KeyboardLayout, widget.TextBox),
    ):
        if hasattr(w, "decorations"):
            casted_w = cast("HasDecorations", w)
            casted_w.decorations = GROUP_DECORATION["decorations"]

# Duplicate widgets_1 into widgets_2 with specific conditions
widgets_2 = []
widgets_3 = []
sm_spacer = small_spacer(length=MARGIN_SIZE)
st_spacer = stretch_spacer()
for w in widgets_1:
    widgets_2.append(w)
    widgets_3.append(w)

# Insert spacers into the widget lists
i = 0
while i < len(widgets_1):
    w = widgets_1[i]
    match w.name:
        case "systray":
            widgets_1.insert(i, st_spacer)
            i += 2
        case "battery":
            widgets_1.insert(i, sm_spacer)
            widgets_1.insert(i + 2, pipe())
            i += 3
        case "battery_icon":
            i += 1
        case "bt_battery":
            widgets_1.insert(i, sm_spacer)
            i += 2
        case "current_layout_icon":
            widgets_1.insert(i + 1, sm_spacer)
            i += 2
        case "groupbox":
            widgets_1.insert(i + 1, sm_spacer)
            i += 2
        case "os_logo":
            widgets_1.insert(i + 1, sm_spacer)
            i += 2
        case _:
            i += 1

i = 0
while i < len(widgets_2):
    w = widgets_2[i]
    match w.name:
        case "battery_icon":
            i += 1
        case "bt_battery":
            widgets_2.insert(i, next(item for item in widgets_1 if item.name == "battery_sep"))
            i += 2
        case "powermenu":
            break
        case _:
            i += 1

i = 0
while i < len(widgets_3):
    w = widgets_3[i]
    match w.name:
        case "battery_icon":
            i += 1
        case "bt_battery":
            widgets_3.insert(i, next(item for item in widgets_1 if item.name == "battery_sep"))
            i += 2
        case "powermenu":
            break
        case _:
            i += 1
