from psutil import sensors_temperatures
from qtile_extras import widget

from modules.settings import colors, text_font


def cpu_temp():
    return sensors_temperatures()["k10temp"][0].current


class CPUTemp(widget.GenPollText):
    defaults = [
        ("update_interval", 5, ""),
        ("padding", 10, ""),
        ("font", text_font, ""),
        ("fontsize", 34, ""),
        ("foreground", colors["darkblue"], ""),
    ]

    def __init__(self, **config):
        widget.GenPollText.__init__(self, **config)
        self.add_defaults(CPUTemp.defaults)

    def poll(self):
        data = int(cpu_temp())
        self.foreground = colors["red"] if data > 65 else colors["lightgreen"]
        return f"{data}°C"
