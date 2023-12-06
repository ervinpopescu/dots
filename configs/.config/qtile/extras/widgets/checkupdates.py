import subprocess

from libqtile.log_utils import logger
from modules.settings import colors
from qtile_extras import widget


def chkup():
    try:
        num = len(
            [
                line
                for line in subprocess.check_output(
                    "apt-get -q -y --ignore-hold --allow-change-held-packages --allow-unauthenticated -s dist-upgrade".split()
                )
                .decode("utf-8")
                .splitlines()
                if "Inst" in line
            ]
        )

        return str(num)
    except subprocess.CalledProcessError as e:
        if e.returncode == 0:
            return str(num)
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
