from libqtile.lazy import lazy
from qtile_extras import widget

from modules.functions import set_layout_all
from modules.settings import colors


current_layout_icon = widget.CurrentLayoutIcon(
    padding=13,
    scale=0.8,
    mouse_callbacks={
        "Button2": set_layout_all(),
        "Button3": lazy.spawn("/home/ervin/bin/rofi_layout.py"),
    },
    use_mask=True,
    foreground=colors["darkblue"],
)
