import copy
from qtile_extras import widget
from libqtile.widget.base import _Widget
from extras.widgets import Battery, BtBattery, WidgetBox
from modules.decorations import decorations
from modules.settings import settings, colors

# Local imports
from .os_logo import os_logo
from .current_layout_icon import current_layout_icon
from .github_notif import github_notif
from .group_box import group_box
from .mouse_over_clock import mouse_over_clock
from .os_logo import os_logo
from .powermenu import powermenu
from .separators import small_spacer, stretch_spacer
from .systray import systray
from .task_list import task_list
from .wallpaper import wallpaper
from .widgetbox import widget_box_1, widget_box_2

# Constants
MARGIN_SIZE = settings["margin_size"] // 2 - 2
DECORATIONS = decorations["single_decor"]
GROUP_DECORATIONS = decorations["group_single_decor"]

# Create a list of widgets for the first group
widgets_1: list[_Widget] = [
    os_logo(),
    widget_box_1,
    group_box(),
    current_layout_icon(),
    task_list(),
    systray(),
    widget_box_2,
    github_notif(),
    mouse_over_clock(),
    wallpaper(),
    powermenu(),
]

# Customize decorations for certain widgets
for w in widgets_1:
    if not isinstance(
        w, (Battery, widget.BatteryIcon, widget.Spacer, widget.Systray, widget.TaskList)
    ):
        w.decorations = DECORATIONS["decorations"]

    if isinstance(
        w, (Battery, BtBattery, widget.BatteryIcon, widget.KeyboardLayout, widget.TextBox)
    ):
        w.decorations = GROUP_DECORATIONS["decorations"]

copy_decorations = copy.deepcopy(DECORATIONS["decorations"])
widgets_1[0].decorations = copy_decorations
copy_decorations[0].colour = colors["fg1"]

# Duplicate widgets_1 into widgets_2 with specific conditions
widgets_2 = []
for w in widgets_1:
    if not isinstance(
        w,
        (
            widget.Systray,
            WidgetBox,
            widget.GithubNotifications,
            widget.GroupBox,
        ),
    ):
        copied = copy.copy(w)
        widgets_2.append(copied)
    elif isinstance(w, widget.GroupBox):
        gb = group_box()
        gb.decorations = DECORATIONS["decorations"]
        widgets_2.append(gb)

# Insert Spacer widgets into widgets_1
i = 1
while i < len(widgets_1):
    w = widgets_1[i]

    if w.name == "second_widgetbox" or isinstance(w, widget.Systray):
        widgets_1.insert(i, stretch_spacer())
        i += 2
    elif "powermenu" in w.name:
        break
    else:
        widgets_1.insert(i, small_spacer(MARGIN_SIZE))
        i += 2

# Insert Spacer widgets into widgets_2
i = 1
while i < len(widgets_2):
    w = widgets_2[i]

    if w.name == "mouseoverclock":
        widgets_2.insert(i, stretch_spacer())
        i += 2
    elif "powermenu" in w.name:
        break
    else:
        widgets_2.insert(i, small_spacer(MARGIN_SIZE))
        i += 2

# Define public exports
__all__ = [
    "widgets_1",
    "widgets_2",
]
