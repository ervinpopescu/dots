from qtile_extras import widget

from modules.decorations import decorations


def systray():
    return widget.Systray(
        icon_size=40,
        padding=20,
        # **decorations["single_decor"],
    )
