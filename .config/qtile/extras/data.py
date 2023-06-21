import subprocess
from operator import mod

from qtile_extras import widget

from modules.settings import colors


def get_uptime():
    with open("/proc/uptime", "r") as f:
        seconds = int(float(f.readline().split()[0]))
        days = seconds // 86400
        hours = mod(seconds, 86400) // 3600
    if days == 0:
        return f"up {hours}h"
    if hours == 24:
        return f"up {days}d"
    return f"up {days}d,{hours}h"


class Data(widget.GenPollText):
    defaults = [
        ("update_interval", 3600, "Update interval in seconds"),
        ("padding", 5, ""),
        ("fontsize", 13, ""),
        ("foreground", colors["fg2"], ""),
        (
            "func",
            lambda: str(get_uptime()),
        ),
    ]

    def __init__(self, **config):
        widget.GenPollText.__init__(self, **config)
        self.add_defaults(Data.defaults)
