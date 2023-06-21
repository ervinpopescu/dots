import subprocess

from libqtile.log_utils import logger
from qtile_extras import widget

from modules.settings import colors


def chkup():
    try:
        num = str(len(subprocess.check_output("checkupdates").decode("utf-8").splitlines()))
        return num
    except subprocess.CalledProcessError as e:
        if e.returncode == 2:
            return "0"
        elif e.returncode == 0:
            return num
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
        if data == "0":
            self.foreground = colors["lightgreen"]
        else:
            self.foreground = colors["red"]
        return data
