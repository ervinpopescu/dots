import copy

from libqtile.widget.base import _Widget
from qtile_extras import widget

from extras.widgets import Battery, BtBattery, TaskList, WidgetBox  # noqa: F401
from modules.decorations import decorations
from modules.settings import colors
from modules.widgets.current_layout_icon import current_layout_icon
from modules.widgets.github_notif import github_notif
from modules.widgets.group_box import group_box
from modules.widgets.mouse_over_clock import mouse_over_clock
from modules.widgets.os_logo import os_logo
from modules.widgets.powermenu import powermenu
from modules.widgets.separators import pipe, small_spacer, stretch_spacer  # noqa: F401
from modules.widgets.systray import systray
from modules.widgets.task_list import task_list
from modules.widgets.wallpaper import wallpaper

# Constants
MARGIN_SIZE = 10 // 2 - 2
SINGLE_DECORATION = decorations["single_decor"]
GROUP_DECORATION = decorations["group_single_decor"]
icon_size = 36 - 12
margin_y = icon_size + 4


def configure_widget(
    widget,
    fontsize_adjustment=None,
    icon_size_adjustment=None,
    margin_adjustment=None,
    scale=None,
    decorations=None,
):
    """Configures widget properties based on the parameters provided."""
    if scale is not None and hasattr(widget, "scale"):
        widget.scale = scale
    if decorations is not None:
        widget.decorations = decorations
    if hasattr(widget, "fontsize") and fontsize_adjustment is not None:
        if widget.fontsize is not None:
            widget.fontsize += fontsize_adjustment
    if hasattr(widget, "font_size") and fontsize_adjustment is not None:
        if widget.font_size is not None:
            widget.font_size += fontsize_adjustment
    if hasattr(widget, "icon_size") and icon_size_adjustment is not None:
        if widget.icon_size is not None:
            widget.icon_size += icon_size_adjustment
    if hasattr(widget, "margin_y") and margin_adjustment is not None:
        if widget.margin_y is not None:
            widget.margin_y += margin_adjustment
    return widget


def add_widget_to_list(
    widget_cls,
    widgets,
    fontsize_adjustment=None,
    icon_size_adjustment=None,
    margin_adjustment=None,
    scale=None,
    decorations=None,
):
    """Creates and configures a widget and appends it to the list."""
    w = widget_cls()
    configure_widget(
        w, fontsize_adjustment, icon_size_adjustment, margin_adjustment, scale, decorations
    )
    widgets.append(w)


def build_widget_lists():
    """Build fresh widget lists for primary and secondary screens.

    Returns (widgets_1, widgets_2, widgets_3) where widgets_1 is for the
    primary screen (full-size bar, includes Systray) and widgets_2/3 are
    for secondary screens (no Systray — X11 only allows one per session).
    """
    sm_spacer = small_spacer(length=MARGIN_SIZE)

    # --- Primary screen widgets ---
    widgets_1: list[_Widget] = [
        os_logo(),
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
        github_notif(),
        mouse_over_clock(),
        wallpaper(),
        powermenu(),
    ]

    for w in widgets_1:
        if not isinstance(
            w, (Battery, widget.BatteryIcon, widget.Spacer, widget.Systray, widget.TaskList)
        ):
            if hasattr(w, "decorations"):
                w.decorations = SINGLE_DECORATION["decorations"]
        if isinstance(
            w,
            (Battery, BtBattery, widget.BatteryIcon, widget.KeyboardLayout, widget.TextBox),
        ):
            if hasattr(w, "decorations"):
                w.decorations = GROUP_DECORATION["decorations"]

    # --- Secondary screen widgets (no Systray, replaced by stretch spacer) ---
    widgets_2: list = []
    widgets_3: list = []

    for w in widgets_1:
        match w:
            case widget.Systray():
                # Systray can only exist on one screen in X11; omit from secondary
                continue
            case widget.TaskList():
                add_widget_to_list(task_list, widgets_2)
                add_widget_to_list(task_list, widgets_3)
            case widget.GroupBox():
                add_widget_to_list(
                    group_box,
                    widgets_2,
                    decorations=SINGLE_DECORATION["decorations"],
                )
                add_widget_to_list(
                    group_box,
                    widgets_3,
                    decorations=SINGLE_DECORATION["decorations"],
                )
            case _:
                w2 = copy.copy(w)
                w3 = copy.copy(w)
                if hasattr(w, "decorations"):
                    w2.decorations = SINGLE_DECORATION["decorations"]
                    w3.decorations = SINGLE_DECORATION["decorations"]
                widgets_2.append(w2)
                widgets_3.append(w3)

    # --- Spacers for primary bar ---
    i = 1
    while i < len(widgets_1):
        w = widgets_1[i]
        match w.name:
            case "systray":
                widgets_1.insert(i, stretch_spacer())
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
            case "powermenu":
                break
            case _:
                widgets_1.insert(i, sm_spacer)
                i += 2

    # --- Spacers for secondary bars ---
    def _insert_secondary_spacers(widget_list):
        i = 1
        while i < len(widget_list):
            w = widget_list[i]
            match w.name:
                case "github_notif":
                    widget_list.insert(i, stretch_spacer())
                    i += 2
                case "current_layout_icon":
                    widget_list.insert(i + 1, sm_spacer)
                    i += 2
                case "groupbox":
                    widget_list.insert(i + 1, sm_spacer)
                    i += 2
                case "os_logo":
                    widget_list.insert(i + 1, sm_spacer)
                    i += 2
                case "powermenu":
                    break
                case _:
                    widget_list.insert(i, sm_spacer)
                    i += 2

    _insert_secondary_spacers(widgets_2)
    _insert_secondary_spacers(widgets_3)

    return widgets_1, widgets_2, widgets_3


__all__ = ["build_widget_lists", "Battery", "BtBattery", "TaskList", "WidgetBox"]
