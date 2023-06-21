from libqtile.lazy import lazy

from extras import Weather
from modules.popups import location, weather_popup
from modules.settings import text_font


def weather():
    return Weather(
        font=text_font,
        fontsize=34,
        appkey="ce4579dd88a8d4877a8c23f2a10d61cc",
        format="{icon}{temp:.0f}°{units_temperature}",
        location=location(),
        mouse_callbacks={
            "Button1": weather_popup(),
            "Button3": lazy.widget["weather"].force_update(),
        },
        padding=10,
    )
