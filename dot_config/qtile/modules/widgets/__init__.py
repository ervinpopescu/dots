from typing import TYPE_CHECKING, Any, Protocol, cast

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
from modules.widgets.separators import pipe, small_spacer, stretch_spacer
from modules.widgets.systray import systray
from modules.widgets.task_list import task_list
from modules.widgets.wallpaper import wallpaper

if TYPE_CHECKING:

    class HasDecorations(Protocol):
        decorations: Any


# Constants
MARGIN_SIZE = 10 // 2 - 2
SINGLE_DECORATION = decorations["single_decor"]
GROUP_DECORATION = decorations["group_single_decor"]
icon_size = 36 - 12
margin_y = icon_size + 4


def _apply_decorations(widgets_list):
    for w in widgets_list:
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


def _insert_primary_spacers(widgets_list):
    sm = small_spacer(length=MARGIN_SIZE)
    st = stretch_spacer()
    i = 0
    while i < len(widgets_list):
        w = widgets_list[i]
        match w.name:
            case "systray":
                widgets_list.insert(i, st)
                i += 2
            case "battery":
                widgets_list.insert(i, sm)
                widgets_list.insert(i + 2, pipe())
                i += 3
            case "battery_icon":
                i += 1
            case "bt_battery":
                widgets_list.insert(i, sm)
                i += 2
            case "current_layout_icon":
                widgets_list.insert(i + 1, sm)
                i += 2
            case "groupbox":
                widgets_list.insert(i + 1, sm)
                i += 2
            case "os_logo":
                widgets_list.insert(i + 1, sm)
                i += 2
            case _:
                i += 1


def _insert_secondary_spacers(widgets_list):
    sm = small_spacer(length=MARGIN_SIZE)
    st = stretch_spacer()
    i = 0
    while i < len(widgets_list):
        w = widgets_list[i]
        match w.name:
            case "github_notif":
                widgets_list.insert(i, st)
                i += 2
            case "current_layout_icon":
                widgets_list.insert(i + 1, sm)
                i += 2
            case "groupbox":
                widgets_list.insert(i + 1, sm)
                i += 2
            case "os_logo":
                widgets_list.insert(i + 1, sm)
                i += 2
            case _:
                i += 1


def _make_primary() -> list[_Widget]:
    return [
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


def _make_secondary() -> list[_Widget]:
    """Secondary screen bar: like primary but without the Systray."""
    return [
        os_logo(),
        group_box(),
        current_layout_icon(),
        task_list(),
        github_notif(),
        mouse_over_clock(),
        wallpaper(),
        powermenu(),
    ]


def build_widget_lists():
    """Build fresh widget lists for primary and secondary screens.

    Returns (widgets_1, widgets_2, widgets_3).  widgets_1 is for the primary
    screen (includes Systray).  widgets_2/3 are for secondary screens (no
    Systray, since X11 only allows one Systray per session).
    """
    widgets_1 = _make_primary()
    widgets_2 = _make_secondary()
    widgets_3 = _make_secondary()

    _apply_decorations(widgets_1)
    _apply_decorations(widgets_2)
    _apply_decorations(widgets_3)

    _insert_primary_spacers(widgets_1)
    _insert_secondary_spacers(widgets_2)
    _insert_secondary_spacers(widgets_3)

    return widgets_1, widgets_2, widgets_3


__all__ = ["build_widget_lists", "Battery", "BtBattery", "TaskList", "WidgetBox"]
