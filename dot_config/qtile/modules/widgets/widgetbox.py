from extras.widgets import WidgetBox
from modules.decorations import decorations
from modules.settings import colors

from .separators import small_spacer
from .uptime import uptime
from .weather import weather

ms = 10 // 4
decor = decorations["single_decor"]
group_decor = decorations["group_single_decor"]


def make_widget_box_1():
    return WidgetBox(
        name="first_widgetbox",
        fontsize=20,
        foreground=colors["darkblue"],
        padding=10,
        start_opened=True,
        text_closed="",
        text_open="",
        widgets=[
            small_spacer(length=ms),
            small_spacer(length=ms),
            # kbd_layout(),
            # kbd_layout_icon(),
        ],
    )


def make_widget_box_2():
    return WidgetBox(
        name="second_widgetbox",
        fontsize=20,
        close_button_location="right",
        foreground=colors["darkblue"],
        padding=10,
        start_opened=False,
        text_closed="",
        text_open="",
        widgets=[
            weather(),
            uptime(),
            small_spacer(length=ms),
        ],
    )


# Module-level instances kept for backward compatibility
widget_box_1 = make_widget_box_1()
widget_box_2 = make_widget_box_2()
