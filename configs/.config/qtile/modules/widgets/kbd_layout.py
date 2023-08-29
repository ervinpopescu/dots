from qtile_extras import widget

from modules.settings import colors, settings

kbd_layout = widget.KeyboardLayout(
    configured_keyboards=["us", "ro std"],
    display_map={"us": "us", "ro std": "ro"},
    fmt="{}",
    font=settings["text_font"],
    fontsize=settings["font_size"],
    foreground=colors["darkblue"],
    padding=10,
)
