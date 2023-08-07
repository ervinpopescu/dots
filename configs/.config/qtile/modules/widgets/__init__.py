from libqtile.lazy import lazy
from qtile_extras import widget

from extras.widgets import Battery, BtBattery
from modules.decorations import decorations
from modules.path import config_path
from modules.settings import colors, margin_size, text_font

from .arch_logo import arch_logo
from .battery import battery
from .battery_icon import battery_icon
from .bt_bat import bt_bat
from .check_updates import check_updates
from .cpu_temp import cpu_temp
from .current_layout_icon import current_layout_icon
from .github_notif import github_notif
from .group_box import group_box
from .kbd_layout import kbd_layout
from .kbd_layout_icon import kbd_layout_icon
from .mouse_over_clock import mouse_over_clock
from .powermenu import powermenu
from .separators import small_spacer, stretch_spacer
from .systray import systray
from .task_list import task_list
from .uptime import uptime
from .wallpaper import wallpaper
from .weather import weather

# from .maximize import maximize
# from .music import music
# from .widgetbox import widgetbox_1, widgetbox_2

ms = margin_size // 4
decor = decorations["single_decor"]
group_decor = decorations["group_single_decor"]
first_stretch_spacer = stretch_spacer()
second_stretch_spacer = stretch_spacer()

widgets_1 = [
    arch_logo,
    # small_spacer(),
    # music,
    small_spacer(),
    check_updates,
    small_spacer(),
    uptime,
    # small_spacer(),
    # widget_box_1,
    small_spacer(),
    group_box,
    small_spacer(),
    current_layout_icon,
    small_spacer(),
    task_list,
    first_stretch_spacer,
    systray,
    second_stretch_spacer,
    # widget_box_2,
    small_spacer(),
    weather,
    small_spacer(),
    cpu_temp,
    small_spacer(),
    kbd_layout,
    kbd_layout_icon,
    small_spacer(),
    github_notif,
    small_spacer(),
    battery,
    battery_icon,
    small_spacer(),
    bt_bat,
    small_spacer(),
    mouse_over_clock,
    small_spacer(),
    wallpaper,
    small_spacer(),
    powermenu,
]

ss1_index = widgets_1.index(first_stretch_spacer)
ss2_index = widgets_1.index(second_stretch_spacer)

for w in widgets_1:
    if not isinstance(w, (widget.Systray, widget.Spacer, Battery, widget.BatteryIcon)):
        w.decorations = decor["decorations"]

    if isinstance(w, (Battery, widget.BatteryIcon, widget.TextBox, widget.KeyboardLayout)):
        w.decorations = group_decor["decorations"]

widgets_2 = [
    w for w in widgets_1[:ss1_index] + widgets_1[ss2_index:] if not isinstance(w, widget.Systray)
]

__all__ = [
    "widgets_1",
    "widgets_2",
]
