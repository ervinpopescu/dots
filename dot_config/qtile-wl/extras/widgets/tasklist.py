from libqtile.config import Match
from qtile_extras import widget


class TaskList(widget.TaskList):
    defaults = []

    def __init__(self, **config):
        widget.TaskList.__init__(self, **config)
        self.add_defaults(TaskList.defaults)
        self.add_callbacks({"Button2": self.close_window})

    def close_window(self):
        if self.clicked:
            window = self.clicked
            window.kill()

    def update(self, window=None):
        if not window or window in self.windows:
            self.draw()

    @property
    def windows(self):
        if self.qtile.core.name == "wayland":
            windows = [
                w
                for w in self.bar.screen.group.windows
                if w.match(~Match(title="qalttab"))
            ]
            return windows
        return self.bar.screen.group.windows
