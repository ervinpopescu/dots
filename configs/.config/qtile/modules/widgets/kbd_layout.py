from qtile_extras import widget

from modules.settings import colors, text_font


kbd_layout = widget.KeyboardLayout(
    configured_keyboards=["us", "ro std"],
    display_map={"us": "us", "ro std": "ro"},
    fmt="{}",
    font=text_font,
    fontsize=36,
    foreground=colors["darkblue"],
    padding=10,
)
