from libqtile.lazy import lazy

from extras.widgets import Weather
from modules.popups import location, weather_popup
from modules.settings import settings


def weather():
    return Weather(
        font=settings["text_font"],
        fontsize=settings["font_size"],
        appkey="REDACTED_OPENWEATHER_KEY",
        format="{icon}{temp:.0f}°{units_temperature}",
        location=location(),
        mouse_callbacks={
            "Button1": weather_popup(),
            "Button3": lazy.widget["weather"].force_update(),
        },
        padding=10,
    )
