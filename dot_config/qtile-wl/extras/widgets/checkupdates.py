import shutil
import subprocess

from libqtile.widget.base import BackgroundPoll
from qtile_extras.widget import modify

from modules.settings import colors


def chkup():
    try:
        num = len(subprocess.check_output("checkupdates").decode("utf-8").splitlines())
        return str(num)
    except subprocess.CalledProcessError as e:
        if e.returncode == 0:
            return "0"
        elif e.returncode == 2:
            return "0"
        else:
            try:
                shutil.rmtree("/tmp/checkup-db-1000")
            except Exception:
                pass
            return "0"
    except Exception:
        return "0"


class CheckUpdates(BackgroundPoll):
    defaults = [
        ("update_interval", 3600, "Update interval in seconds"),
        ("padding", 5, ""),
        ("fontsize", 12, ""),
        ("foreground", colors["fg2"], ""),
    ]

    def __init__(self, **config):
        super().__init__("0", **config)
        modify(CheckUpdates, initialise=False)
        self.add_defaults(CheckUpdates.defaults)

    def poll(self):
        data = chkup()
        self.foreground = colors["lightgreen"] if data == "0" else colors["red"]
        if self.layout:
            self.layout.colour = self.foreground
        return data

