from modules.decorations import decorations
from qtile_extras import widget


def systray():
    return widget.Systray(
        icon_size=32,
        padding=20,
        # **decorations["systray_decor"],
    )
