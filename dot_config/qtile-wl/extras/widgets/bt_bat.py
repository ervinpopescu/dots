import os
import subprocess

from libqtile.widget.base import BackgroundPoll
from qtile_extras.widget import modify

from modules.settings import colors, settings


class BtBattery(BackgroundPoll):
    defaults = [
        ("update_interval", 60, "Update interval in seconds"),
        ("fontsize", 20, ""),
        ("foreground", colors.get("fg2", "#ffffff"), ""),
    ]

    def __init__(self, **config):
        super().__init__("", **config)
        modify(BtBattery, initialise=False)
        self.add_defaults(BtBattery.defaults)
        self.add_callbacks({"Button3": self.force_update})

    def poll(self):
        try:
            data = (
                subprocess.check_output(
                    os.path.join(os.environ["HOME"], "bin", "bt-bat.py"),
                    timeout=10,
                )
                .decode()
                .strip()
            )
        except Exception:
            return " err"

        if data == "":
            self.foreground = colors.get("fg0", "#ffffff")
            return ""

        left = None
        right = None
        case = None
        try:
            val = int(data)
            self.fontsize = settings.font_size + 4
            if val > 10:
                self.foreground = colors.get("lightgreen", "#00ff00")
            else:
                self.foreground = colors.get("red", "#ff0000")
            if self.layout:
                self.layout.colour = self.foreground
            return f" {val}"
        except ValueError:
            try:
                data_list = data.split(",")
                left = int(data_list[0].replace("L:", ""))
                right = int(data_list[1].replace("R:", ""))
                case = int(data_list[2].replace("C:", ""))

                if left > 10 and right > 10 and case > 30:
                    self.foreground = colors.get("lightgreen", "#00ff00")
                elif left != -1 and right != -1:
                    self.foreground = colors.get("red", "#ff0000")

                if case == -1:
                    self.foreground = colors.get("lightgreen", "#00ff00")
                    data = data.replace(",C:-1", "")

                if self.layout:
                    self.layout.colour = self.foreground
                return f" {data}"
            except Exception:
                return f" {data}"
