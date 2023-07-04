import subprocess

from libqtile.log_utils import logger
from qtile_extras import widget

from modules.settings import colors


def chkup():
    try:
        return str(
            len(
                subprocess.check_output("checkupdates")
                .decode("utf-8")
                .splitlines()
            )
        )
    except subprocess.CalledProcessError as e:
        if e.returncode == 0:
            return num
        elif e.returncode == 2:
            return "0"
        else:
            return "Error"


class CheckUpdates(widget.GenPollText):
    defaults = [
        ("update_interval", 3600, "Update interval in seconds"),
        ("padding", 5, ""),
        ("fontsize", 12, ""),
        ("foreground", colors["fg2"], ""),
    ]

    def __init__(self, **config):
        widget.GenPollText.__init__(self, **config)
        self.add_defaults(CheckUpdates.defaults)

    def poll(self):
        data = chkup()
        self.foreground = colors["lightgreen"] if data == "0" else colors["red"]
        return data
