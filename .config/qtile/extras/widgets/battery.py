import os
import subprocess

import pydbus
from libqtile.widget import base
from psutil import sensors_battery
from qtile_extras import widget

from modules.settings import colors


class Battery(widget.GenPollText):
    defaults = [
        ("update_interval", 1, "Update interval in seconds"),
        ("fontsize", 34, ""),
        ("foreground", colors["fg2"], ""),
    ]

    def __init__(self, **config):
        widget.GenPollText.__init__(self, **config)
        self.add_defaults(Battery.defaults)
        self.add_defaults(base.MarginMixin.defaults)

    def func(self):
        return int(sensors_battery().percent)

    def poll(self):
        if not self.func:
            return "You need a poll function"
        data = self.func()
        self.foreground = colors["lightgreen"] if data > 10 else colors["red"]
        return f"{data}%"
