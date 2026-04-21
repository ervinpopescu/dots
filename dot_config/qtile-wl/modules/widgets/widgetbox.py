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


def make_widget_box_1():
    sm = small_spacer(length=ms)
    wb = WidgetBox(
        name="first_widgetbox",
        fontsize=25,
        foreground=colors["darkblue"],
        padding=10,
        start_opened=True,
        text_closed="",
        text_open="",
        widgets=[sm, check_updates(), sm, uptime()],
    )
    for w in wb.widgets:
        if not isinstance(w, (widget.Spacer, widget.TextBox, widget.KeyboardLayout)):
            w.decorations = decor["decorations"]
        if isinstance(w, (widget.TextBox, widget.KeyboardLayout)):
            w.decorations = group_decor["decorations"]
    return wb


def make_widget_box_2():
    sm = small_spacer(length=ms)
    wb = WidgetBox(
        name="second_widgetbox",
        fontsize=25,
        close_button_location="right",
        foreground=colors["darkblue"],
        padding=10,
        start_opened=True,
        text_closed="",
        text_open="",
        widgets=[weather(), sm, cpu_temp(), sm, kbd_layout(), kbd_layout_icon(), sm],
    )
    for w in wb.widgets:
        if not isinstance(w, (widget.Spacer, widget.TextBox, widget.KeyboardLayout)):
            w.decorations = decor["decorations"]
        if isinstance(w, (widget.TextBox, widget.KeyboardLayout)):
            w.decorations = group_decor["decorations"]
    return wb
