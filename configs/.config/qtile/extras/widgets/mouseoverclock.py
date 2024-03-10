from qtile_extras import widget


class MouseOverClock(widget.Clock):
    defaults = [
        (
            "long_format",
            "%d/%m/%y %H:%M",
            "Format to show when mouse is over widget.",
        ),
    ]

    def __init__(self, **config):
        widget.Clock.__init__(self, **config)
        self.add_defaults(MouseOverClock.defaults)
        self.short_format = self.format

    def mouse_enter(self, *args):
        self.format = self.long_format
        self.bar.draw()

    def mouse_leave(self, *args):
        self.format = self.short_format