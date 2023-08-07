from qtile_extras import widget

from extras.widgets import WidgetBox
from modules.settings import colors
from modules.widgets import decor, group_decor

from .check_updates import check_updates
from .cpu_temp import cpu_temp
from .kbd_layout import kbd_layout
from .kbd_layout_icon import kbd_layout_icon
from .separators import small_spacer
from .uptime import uptime
from .weather import weather

widgetbox_1 = WidgetBox(
    fontsize=40,
    foreground=colors["darkblue"],
    padding=10,
    # start_opened=True,
    text_closed="",
    text_open="",
    widgets=[
        small_spacer(),
        check_updates,
        small_spacer(),
        uptime,
    ],
)

widgetbox_2 = WidgetBox(
    fontsize=40,
    close_button_location="right",
    foreground=colors["darkblue"],
    padding=10,
    # start_opened=True,
    text_closed="",
    text_open="",
    widgets=[
        small_spacer(),
        weather,
        small_spacer(),
        cpu_temp,
        small_spacer(),
        kbd_layout,
        kbd_layout_icon,
        small_spacer(),
    ],
)

for w in widgetbox_1.widgets:
    if not isinstance(w, (widget.Spacer, widget.TextBox, widget.KeyboardLayout)):
        w.decorations = decor["decorations"]
    if isinstance(w, (widget.TextBox, widget.KeyboardLayout)):
        w.decorations = group_decor["decorations"]

for w in widgetbox_2.widgets:
    if not isinstance(w, (widget.Spacer, widget.TextBox, widget.KeyboardLayout)):
        w.decorations = decor["decorations"]
    if isinstance(w, (widget.TextBox, widget.KeyboardLayout)):
        w.decorations = group_decor["decorations"]
