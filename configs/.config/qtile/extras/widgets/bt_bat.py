import os
import subprocess

import pydbus
from libqtile.widget import base
from qtile_extras import widget

from modules.settings import colors


class BtBattery(widget.GenPollText):
    defaults = [
        ("update_interval", 1, "Update interval in seconds"),
        ("fontsize", 34, ""),
        ("foreground", colors["fg2"], ""),
    ]

    def __init__(self, **config):
        widget.GenPollText.__init__(self, **config)
        self.add_defaults(BtBattery.defaults)
        self.add_defaults(base.MarginMixin.defaults)

    def poll(self):
        data = (
            subprocess.check_output(
                os.path.join(os.environ["HOME"], "bin", "bt-bat.sh")
            )
            .decode("utf-8")
            .strip("\n")
        )
        if data == "":
            return ""
        self.foreground = colors["lightgreen"] if int(data) > 10 else colors["red"]
        return f" {data}%"
