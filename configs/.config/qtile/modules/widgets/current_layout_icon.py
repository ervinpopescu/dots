import os

from libqtile.lazy import lazy
from modules.functions import set_layout_all
from modules.settings import colors
from qtile_extras import widget
from modules.settings import colors, config_path


def current_layout_icon():
    return widget.CurrentLayoutIcon(
        padding=13,
        scale=0.8,
        mouse_callbacks={
            "Button2": set_layout_all(),
            "Button3": lazy.spawn(os.path.join(config_path, "scripts", "rofi_layout.py")),
        },
        use_mask=True,
        foreground=colors["darkblue"],
    )
