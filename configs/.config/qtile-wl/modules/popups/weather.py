import subprocess

from libqtile.log_utils import logger
from libqtile.lazy import lazy
from qtile_extras.popup.toolkit import PopupAbsoluteLayout, PopupText

from modules.functions import location
from modules.settings import settings


@lazy.function
def weather_popup(qtile):
    wttr = (
        subprocess.check_output(
            [
                "/home/ervin/bin/wttr.sh",
                location(),
                "?M?T?0",
            ]
        )
        .decode("utf-8")
        .splitlines()
    )
    wttr.pop(0)
    wttr.pop(0)
    wttr = "\n".join(wttr)
    controls = [
        PopupText(
            font=settings["text_font"],
            pos_x=10,
            pos_y=10,
            fontsize=25,
            foreground="000000",
            text=wttr,
            width=500,
            height=300,
        )
    ]
    layout = PopupAbsoluteLayout(
        qtile,
        width=500,
        height=300,
        controls=controls,
        opacity=0.96,
        background=qtile.widgets_map["weather"].foreground,
        initial_focus=None,
    )
    widget_offset = qtile.widgets_map["weather"].info()["offset"]
    screen_info = qtile.core.get_screen_info()
    # screen_width = min([screen_info[i].width for i in range(len(screen_info))])
    screen_height = min([screen_info[i].height for i in range(len(screen_info))])
    if not layout.configured:
        layout._configure(qtile)
    layout.popup.win.window.set_property("ROUNDED_CORNERS_EXCLUDE", 0, "CARDINAL", 32)
    layout.show(
        # x=2880 - layout.width - settings["margin_size"],
        x=widget_offset + settings["margin_size"],
        y=screen_height
        - layout.height
        - qtile.current_screen.bottom.info()["size"]
        - settings["margin_size"],
        warp_pointer=True,
    )
