from libqtile.widget.open_weather import (
    OpenWeatherResponseError,
    _OpenWeatherResponseParser,
)

from modules.settings import colors
from qtile_extras.widget import OpenWeather


class Weather(OpenWeather):
    defaults = [
        ("appkey", "ce4579dd88a8d4877a8c23f2a10d61cc", ""),
        ("padding", 5, ""),
        ("fontsize", 12, ""),
        ("foreground", "#D9E0EE", ""),
        ("format", "{icon}{main_feels_like:.0f}°{units_temperature}", ""),
    ]

    def __init__(self, **config):
        OpenWeather.__init__(self, **config)
        self.add_defaults(Weather.defaults)

    def parse(self, response):
        try:
            rp = _OpenWeatherResponseParser(response, self.dateformat, self.timeformat)
        except OpenWeatherResponseError as e:
            return f"Error {e.resp_code}"

        data = rp.data
        data["units_temperature"] = "C" if self.metric else "F"
        data["units_wind_speed"] = "Km/h" if self.metric else "m/h"
        data["icon"] = self.symbols.get(data["weather_0_icon"], self.symbols["Unknown"])
        if data["temp"] >= 15:
            self.foreground = colors["yellow"]
        else:
            self.foreground = colors["lightblue"]
        return self.format.format(**data)
