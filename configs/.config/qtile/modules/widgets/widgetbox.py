from extras.widgets import WidgetBox
from modules.decorations import decorations
from modules.settings import colors, settings
from modules.widgets import decor, group_decor
from qtile_extras import widget

from .check_updates import check_updates
from .kbd_layout import kbd_layout
from .kbd_layout_icon import kbd_layout_icon
from .separators import small_spacer
from .uptime import uptime
from .weather import weather

ms = settings["margin_size"] // 4
decor = decorations["single_decor"]
group_decor = decorations["group_single_decor"]
widget_box_1 = WidgetBox(
    name="first_widgetbox",
    fontsize=40,
    foreground=colors["darkblue"],
    padding=10,
    # start_opened=True,
    text_closed="",
    text_open="",
    widgets=[
        small_spacer(length=ms),
        check_updates(),
        small_spacer(length=ms),
        uptime(),
    ],
)
widget_box_2 = WidgetBox(
    name="second_widgetbox",
    fontsize=40,
    close_button_location="right",
    foreground=colors["darkblue"],
    padding=10,
    # start_opened=True,
    text_closed="",
    text_open="",
    widgets=[
        small_spacer(length=ms),
        weather(),
        small_spacer(ms),
        small_spacer(ms),
        kbd_layout(),
        kbd_layout_icon(),
        small_spacer(length=ms),
    ],
)

for w in widget_box_1.widgets:
    if not isinstance(w, (widget.Spacer, widget.TextBox, widget.KeyboardLayout)):
        w.decorations = decor["decorations"]
    if isinstance(w, (widget.TextBox, widget.KeyboardLayout)):
        w.decorations = group_decor["decorations"]

for w in widget_box_2.widgets:
    if not isinstance(w, (widget.Spacer, widget.TextBox, widget.KeyboardLayout)):
        w.decorations = decor["decorations"]
    if isinstance(w, (widget.TextBox, widget.KeyboardLayout)):
        w.decorations = group_decor["decorations"]
