import os
import subprocess
from types import NoneType

# from libqtile.command.base import expose_command
from libqtile.widget import base
from qtile_extras import widget

from modules.settings import colors, settings


class BtBattery(widget.GenPollText):
    defaults = [
        ("update_interval", 60, "Update interval in seconds"),
        ("fontsize", 20, ""),
        ("foreground", colors["fg2"], ""),
    ]

    def __init__(self, **config):
        base.ThreadPoolText.__init__(self, **config)
        self.add_defaults(BtBattery.defaults)
        self.add_callbacks({"Button3": self.force_update})

    def poll(self):  # type: ignore
        data = (
            subprocess.check_output(
                # os.path.join(os.environ["HOME"], "bin", "bt-bat.sh"),
                os.path.join(os.environ["HOME"], "bin", "bt-bat.py"),
                timeout=10,
            )
            .decode()
            .strip()
        )
        if data == "":
            self.foreground = colors["fg0"]
            return ""
        left: int | NoneType = None
        right: int | NoneType = None
        case: int | NoneType = None
        try:
            data = int(data)
            self.fontsize = settings.font_size + 4
            if data > 10:
                self.foreground = colors["lightgreen"]
            else:
                self.foreground = colors["red"]
        except ValueError:
            data_list = data.split(",")  # type: ignore
            left = int(data_list[0].replace("L:", ""))
            right = int(data_list[1].replace("R:", ""))
            case = int(data_list[2].replace("C:", ""))
            if left > 10 and right > 10 and case > 30:  # type: ignore
                self.foreground = colors["lightgreen"]
            elif left != -1 and right != -1:
                self.foreground = colors["red"]
            if case == -1:
                self.foreground = colors["lightgreen"]
                data = data.replace(",C:-1", "")  # type: ignore
            # else:
            #     return ""

        # self._configure(self.bar.qtile, self.bar)

        return f" {data}"

    # TODO: IMPLEMENT async_force_update
    # @expose_command()
    def async_force_update(self):
        self.poll()
