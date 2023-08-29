from qtile_extras import widget

from modules.settings import colors, settings

group_box = widget.GroupBox(
    active=colors["darkblue"],
    disable_drag=True,
    font=settings["icon_font"],
    fontsize=settings["font_size"],
    hide_unused=True,
    inactive=colors["bg3"],
    margin_x=10,
    other_screen_border=colors["turquoise"],
    padding_x=5,
    padding_y=5,
    rounded="true",
    this_current_screen_border=colors["darkblue"],
)
