import copy

from libqtile.widget import SwayNC
from libqtile.widget.base import _Widget
from qtile_extras import widget

from extras.widgets import Battery, BatteryIcon, BtBattery
from modules.decorations import decorations
from modules.settings import colors, settings
from modules.widget_names import BATTERY_SEP

from .battery import battery
from .battery_icon import battery_icon
from .bt_bat import bt_bat
from .chord import chord
from .current_layout_icon import current_layout_icon
from .github_notif import github_notif
from .group_box import group_box
from .mouse_over_clock import mouse_over_clock
from .os_logo import os_logo
from .powermenu import powermenu
from .separators import (  # noqa: F401  # stretch_spacer re-exported
    pipe,
    small_spacer,
    stretch_spacer,
)
from .systray import systray
from .task_list import task_list
from .wallpaper import wallpaper
from .widgetbox import make_widget_box_1, make_widget_box_2

# Constants
MARGIN_SIZE = settings.margin_size // 2
SINGLE_DECORATION = decorations["single_decor"]  # type: ignore
GROUP_DECORATION = decorations["group_single_decor"]  # type: ignore


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
    primary screen (full-size bar) and widgets_2/3 are for secondary screens
    (smaller bar with reduced font sizes).
    """

    def sm_spacer():
        return small_spacer(name="sm_sp", length=MARGIN_SIZE)

    battery_inner_spacer = small_spacer(name="bat_in_sp", length=0)
    battery_inner_spacer.decorations = GROUP_DECORATION["decorations"]  # type: ignore

    # --- Primary screen widgets ---
    widgets_1: list[_Widget] = [
        os_logo(),
        make_widget_box_1(),
        group_box(),
        current_layout_icon(),
        task_list(),
        chord(),
        systray(),
        make_widget_box_2(),
        github_notif(),
        battery(),
        battery_icon(),
        bt_bat(),
        mouse_over_clock(),
        wallpaper(),
        powermenu(),
    ]

    for w in widgets_1:
        if not isinstance(
            w, (Battery, widget.BatteryIcon, BtBattery, widget.Spacer, widget.TaskList)
        ) or isinstance(w, SwayNC):
            w.decorations = SINGLE_DECORATION["decorations"]  # type: ignore
        if isinstance(
            w, (Battery, BtBattery, widget.BatteryIcon, widget.KeyboardLayout, widget.TextBox)
        ):
            w.decorations = GROUP_DECORATION["decorations"]  # type: ignore

    # --- Secondary screen widgets (adjusted sizes) ---
    widgets_2: list = []
    widgets_3: list = []
    fontsize_adj = -5
    icon_size_adj = -7

    for w in widgets_1:
        match w:
            case widget.GroupBox():
                add_widget_to_list(
                    group_box,
                    widgets_2,
                    fontsize_adjustment=fontsize_adj - 3,
                    decorations=SINGLE_DECORATION["decorations"],
                )
                add_widget_to_list(
                    group_box,
                    widgets_3,
                    fontsize_adjustment=fontsize_adj - 3,
                    decorations=SINGLE_DECORATION["decorations"],
                )
            case widget.TaskList():
                add_widget_to_list(
                    task_list,
                    widgets_2,
                    fontsize_adjustment=fontsize_adj,
                    margin_adjustment=-3,
                )
                add_widget_to_list(
                    task_list,
                    widgets_3,
                    fontsize_adjustment=fontsize_adj,
                    margin_adjustment=-3,
                )
            case widget.StatusNotifier():
                add_widget_to_list(
                    systray,
                    widgets_2,
                    icon_size_adjustment=icon_size_adj,
                    decorations=SINGLE_DECORATION["decorations"],
                )
                add_widget_to_list(
                    systray,
                    widgets_3,
                    icon_size_adjustment=icon_size_adj,
                    decorations=SINGLE_DECORATION["decorations"],
                )
            case widget.WidgetBox():
                continue
            case widget.BatteryIcon():
                add_widget_to_list(
                    battery_icon,
                    widgets_2,
                    scale=0.8,
                    decorations=GROUP_DECORATION["decorations"],
                )
                add_widget_to_list(
                    battery_icon,
                    widgets_3,
                    scale=0.8,
                    decorations=GROUP_DECORATION["decorations"],
                )
            case _:
                w2 = copy.copy(w)
                w3 = copy.copy(w)
                decor = (
                    GROUP_DECORATION["decorations"]
                    if isinstance(w, (Battery, BtBattery, BatteryIcon))
                    else SINGLE_DECORATION["decorations"]
                )
                configure_widget(w2, fontsize_adjustment=fontsize_adj, decorations=decor)
                configure_widget(w3, fontsize_adjustment=fontsize_adj, decorations=decor)
                widgets_2.append(w2)
                widgets_3.append(w3)

    # --- Spacers for primary bar ---
    i = 1
    while i < len(widgets_1):
        w = widgets_1[i]
        match w.name:
            case "battery":
                widgets_1.insert(i, sm_spacer())
                i += 2
            case "battery_icon":
                i += 1
            case "bt_battery":
                ins = pipe(name=BATTERY_SEP, foreground=colors["bg2"])
                ins.decorations = GROUP_DECORATION["decorations"]  # type: ignore
                widgets_1.insert(i, ins)
                i += 2
            case "powermenu":
                break
            case _:
                widgets_1.insert(i, sm_spacer())
                i += 2

    # --- Spacers for secondary bars ---
    def _insert_secondary_spacers(widget_list):
        battery_sep = next((item for item in widgets_1 if item.name == BATTERY_SEP), None)
        bat_inner_sp = next((item for item in widgets_1 if item.name == "bat_in_sp"), None)
        i = 1
        while i < len(widget_list):
            w = widget_list[i]
            match w.name:
                case "battery":
                    widget_list.insert(i, sm_spacer())
                    if bat_inner_sp:
                        widget_list.insert(i + 2, copy.deepcopy(bat_inner_sp))
                    i += 4
                case "battery_icon":
                    i += 1
                case "bt_battery":
                    if battery_sep:
                        widget_list.insert(i, copy.deepcopy(battery_sep))
                    i += 2
                case "powermenu":
                    break
                case _:
                    widget_list.insert(i, sm_spacer())
                    i += 2

    _insert_secondary_spacers(widgets_2)
    _insert_secondary_spacers(widgets_3)

    return widgets_1, widgets_2, widgets_3


__all__ = ["build_widget_lists"]
