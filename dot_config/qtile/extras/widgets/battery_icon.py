from libqtile.widget.battery import BatteryState, BatteryStatus
from qtile_extras import widget

from modules.settings import colors


class BatteryIcon(widget.BatteryIcon):
    defaults = (
        ("update_interval", 1, "Update interval in seconds"),
        ("fontsize", 34, ""),
        ("foreground", colors["fg2"], ""),
    )

    def __init__(self, **config):
        widget.BatteryIcon.__init__(self, **config)
        self.add_defaults(BatteryIcon.defaults)

    @staticmethod
    def _get_icon_key(status: BatteryStatus) -> str:
        key = "battery"

        percent = status.percent
        if percent < 0.1:
            key += "-caution"
        elif percent < 0.3:
            key += "-low"
        elif percent < 0.8:
            key += "-good"
        else:
            key += "-full"

        state = status.state
        if state == BatteryState.CHARGING:
            key += "-charging"
        elif state == BatteryState.FULL:
            key += "-charged"
        return key
