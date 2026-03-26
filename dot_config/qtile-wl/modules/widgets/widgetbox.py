from qtile_extras import widget

from extras.widgets import WidgetBox
from modules.decorations import decorations
from modules.settings import colors, settings

from .check_updates import check_updates
from .cpu_temp import cpu_temp
from .kbd_layout import kbd_layout
from .kbd_layout_icon import kbd_layout_icon
from .separators import small_spacer
from .uptime import uptime
from .weather import weather

ms = settings.margin_size // 2
decor = decorations["single_decor"]  # type: ignore
group_decor = decorations["group_single_decor"]  # type: ignore
sm_spacer = small_spacer(length=ms)

widget_box_1 = WidgetBox(
    name="first_widgetbox",
    fontsize=25,
    foreground=colors["darkblue"],
    padding=10,
    start_opened=True,
    text_closed="",
    text_open="",
    widgets=[
        sm_spacer,
        check_updates(),
        sm_spacer,
        uptime(),
    ],
)
widget_box_2 = WidgetBox(
    name="second_widgetbox",
    fontsize=25,
    close_button_location="right",
    foreground=colors["darkblue"],
    padding=10,
    start_opened=True,
    text_closed="",
    text_open="",
    widgets=[
        weather(),
        sm_spacer,
        cpu_temp(),
        sm_spacer,
        kbd_layout(),
        kbd_layout_icon(),
        sm_spacer,
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
