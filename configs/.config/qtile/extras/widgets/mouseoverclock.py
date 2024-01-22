import os
import subprocess

import psutil

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
        # subprocess.Popen(["gsimplecal"])

    def mouse_leave(self, *args):
        self.format = self.short_format
        # self.bar.draw()
        # process_name = "gsimplecal"
        # pid = None
        # for proc in psutil.process_iter():
        #     if process_name in proc.name():
        #         pid = proc.pid
        # os.kill(pid, 9)
