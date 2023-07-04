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
        self.percent: int

    def func(self):
        self.percent = int(sensors_battery().percent)
        dbus = pydbus.SystemBus()
        adapter = dbus.get("org.bluez", "/org/bluez/hci0")
        return str(
            f"{self.percent}%"
            + (" " if sensors_battery().power_plugged else "")
            + str(
                subprocess.check_output(
                    os.path.join(os.environ["HOME"], "bin", "bt-bat.sh")
                )
                .decode("utf-8")
                .strip("\n")
                if adapter.Powered
                else ""
            )
        )

    def poll(self):
        if not self.func:
            return "You need a poll function"
        data = self.func()
        self.foreground = colors["lightgreen"] if self.percent > 10 else colors["red"]
        return data
