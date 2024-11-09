from libqtile import hook, qtile
from libqtile.bar import Bar
from libqtile.config import Key, Screen
from libqtile.lazy import lazy
from qtile_extras import widget


@hook.subscribe.startup_once
def autostart():
    qtile.spawn("systray_profile.py", shell=True)


class Systray(widget.StatusNotifier):
    def __init__(self, **config) -> None:
        super().__init__(**config)
        self.add_callbacks({"Button1": self.show_menu}, force=True)
        self.add_callbacks({"Button2": self.show_menu}, force=True)


screens = [
    Screen(
        bottom=Bar(
            widgets=[
                widget.Spacer(),
                Systray(
                    mouse_callbacks={
                        "Button1": lazy.bar["top"].widget["systray"].show_menu()
                    },
                ),
                widget.Spacer(),
            ],
            size=100,
        ),
    )
]

widget_defaults = {
    "fontsize": 40,
    "iconsize": 30,
    "icon_size": 40,
}

keys = [
    Key(
        ["mod4"],
        "Return",
        lazy.spawn("alacritty"),
    ),
    Key(
        ["mod4", "Shift"],
        "q",
        lazy.shutdown(),
    ),
]
keys.extend(
    [
        Key(
            ["control", "mod1"],
            f"f{vt}",
            lazy.core.change_vt(vt).when(func=lambda: qtile.core.name == "wayland"),
            desc=f"Switch to VT{vt}",
        )
        for vt in range(1, 8)
    ]
)
