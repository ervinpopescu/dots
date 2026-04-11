from libqtile import widget

from modules.settings import colors, settings


def bt():
    return widget.Bluetooth(
        default_text="{num_connected_devices} {connected_devices}",
        fontsize=settings.font_size + 4,
        foreground=colors["darkblue"],
    )
