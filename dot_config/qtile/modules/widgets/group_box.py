from qtile_extras import widget

from modules.settings import colors, settings


def group_box():
    return widget.GroupBox(
        active=colors["darkblue"],
        disable_drag=True,
        font=settings["icon_font"],
        fontsize=settings["font_size"],
        hide_unused=True,
        inactive=colors["bg3"],
        margin_x=14,
        other_screen_border=colors["turquoise"],
        # padding_x=3,
        # padding_y=3,
        # rounded="true",
        this_current_screen_border=colors["darkblue"],
    )
