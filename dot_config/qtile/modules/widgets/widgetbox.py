from qtile_extras import widget

from extras.widgets import WidgetBox
from modules.decorations import decorations
from modules.settings import colors

from .kbd_layout import kbd_layout
from .kbd_layout_icon import kbd_layout_icon
from .separators import small_spacer
from .uptime import uptime
from .weather import weather

ms = 10 // 4
decor = decorations["single_decor"]
group_decor = decorations["group_single_decor"]
# widget_box = WidgetBox(
#     name="first_widgetbox",
#     fontsize=20,
#     foreground=colors["darkblue"],
#     padding=10,
#     start_opened=True,
#     text_closed="",
#     text_open="",
#     widgets=[
#         small_spacer(length=ms),
#         kbd_layout(),
#         kbd_layout_icon(),
#         small_spacer(length=ms),
#         weather(),
#         small_spacer(length=ms),
#         uptime(),
#         small_spacer(length=ms),
#     ],
# )
# for w in widget_box.widgets:
#     if not isinstance(w, (widget.Spacer)):
#         if hasattr(w, "decorations"):
#             w.decorations = decor["decorations"]
#
#     if isinstance(w, (widget.KeyboardLayout, widget.TextBox)):
#         if hasattr(w, "decorations"):
#             w.decorations = group_decor["decorations"]

widget_box_1 = WidgetBox(
    name="first_widgetbox",
    fontsize=20,
    foreground=colors["darkblue"],
    padding=10,
    start_opened=True,
    text_closed="",
    text_open="",
    widgets=[
        small_spacer(length=ms),
        small_spacer(length=ms),
        # kbd_layout(),
        # kbd_layout_icon(),
    ],
)
widget_box_2 = WidgetBox(
    name="second_widgetbox",
    fontsize=20,
    close_button_location="right",
    foreground=colors["darkblue"],
    padding=10,
    start_opened=False,
    text_closed="",
    text_open="",
    widgets=[
        weather(),
        uptime(),
        small_spacer(length=ms),
    ],
)
