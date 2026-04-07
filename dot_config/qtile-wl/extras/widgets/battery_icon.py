from libqtile.utils import rgb
from libqtile.widget.battery import BatteryState, BatteryStatus
from qtile_extras import widget

from modules.settings import colors


class BatteryIcon(widget.BatteryIcon):
    defaults = [
        ("update_interval", 60, "Update interval in seconds"),
        ("foreground", colors["fg2"], ""),
    ]

    def __init__(self, **config):
        widget.BatteryIcon.__init__(self, **config)
        self.add_defaults(BatteryIcon.defaults)

    def _get_color(self) -> str:
        icon = self.current_icon
        if "caution" in icon:
            return colors["red"]
        if "low" in icon:
            return colors["orange"]
        if "charged" in icon or "full" in icon:
            return colors["lightgreen"]
        return colors["yellow"]

    def draw(self) -> None:
        self.drawer.clear(self.background or self.bar.background)
        image = self.images[self.current_icon]
        self.drawer.ctx.save()
        self.drawer.ctx.translate(self.padding, (self.bar.size - image.height) // 2)
        r, g, b, a = rgb(self._get_color())
        self.drawer.ctx.set_source_rgba(r, g, b, a)
        self.drawer.ctx.mask(image.pattern)
        self.drawer.ctx.restore()
        self.draw_at_default_position()

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
