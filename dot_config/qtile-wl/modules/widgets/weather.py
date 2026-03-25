from libqtile.lazy import lazy

from extras.widgets import Weather
from modules.functions import location
from modules.popups import weather_popup
from modules.settings import settings
from modules.widget_names import WEATHER


def weather():
    return Weather(
        font=settings["text_font"],
        fontsize=settings["font_size"],
        appkey=settings["openweather_api_key"],
        format="{icon} {temp:.0f}°{units_temperature}",
        location=location(),
        mouse_callbacks={
            "Button1": weather_popup(),
            "Button3": lazy.widget[WEATHER].force_update(),
        },
        padding=10,
        update_interval=5,
    )
