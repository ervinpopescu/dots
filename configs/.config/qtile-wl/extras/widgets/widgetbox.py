# from libqtile import hook

from qtile_extras import widget

from modules.settings import colors


class WidgetBox(widget.WidgetBox):
    defaults = [
        ("fontsize", 40, ""),
        ("padding", 1, ""),
        ("text_closed", "", ""),
        ("text_open", "", ""),
        ("foreground", colors["darkblue"], ""),
        ("fontsize", 40, ""),
        ("start_opened", False),
    ]

    def __init__(self, **config):
        widget.WidgetBox.__init__(self, **config)
        self.add_defaults(WidgetBox.defaults)
        # if self.start_opened:
        #     hook.subscribe.startup(self.toggle)

    @property
    def actual_padding(self):
        return self.fontsize / 2 if self.padding is None else self.padding

    def calculate_length(self):
        return self.layout.width + self.actual_padding * 2

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)

        self.layout.draw(
            (self.actual_padding or 0),
            int(self.bar.height / 2.0 - self.layout.height / 2.0) + 1,
        )

        self.drawer.draw(offsetx=self.offsetx, offsety=self.offsety, width=self.width)
