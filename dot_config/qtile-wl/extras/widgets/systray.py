from qtile_extras import widget


class Systray(widget.StatusNotifier):
    def __init__(self, **config) -> None:
        super().__init__(**config)
        self.add_callbacks({"Button1": self.show_menu})
