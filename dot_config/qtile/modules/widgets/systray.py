from qtile_extras import widget


def systray():
    return widget.Systray(
        icon_size=24,
        padding=20,
        # **decorations["systray_decor"],
    )
