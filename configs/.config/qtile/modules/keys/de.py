from libqtile.config import Key
from libqtile.lazy import lazy
from modules.functions import groupbox_disable_drag
from modules.settings import settings

de_keys = [
    Key(
        [],
        "XF86AudioMute",
        lazy.spawn("/home/ervin/bin/mutevol.sh"),
        desc="Mute audio",
    ),
    Key(
        [],
        "XF86AudioLowerVolume",
        lazy.spawn("/home/ervin/bin/volctl.sh -5%"),
        desc="Lower volume by 5%",
    ),
    Key(
        [],
        "XF86AudioRaiseVolume",
        lazy.spawn("/home/ervin/bin/volctl.sh +5%"),
        desc="Raise volume by 5%",
    ),
    Key(
        ["shift"],
        "XF86AudioLowerVolume",
        lazy.spawn("/home/ervin/bin/mediactl.sh previous"),
        desc="Previous media",
    ),
    Key(
        ["shift"],
        "XF86AudioRaiseVolume",
        lazy.spawn("/home/ervin/bin/mediactl.sh next"),
        desc="Next media",
    ),
    Key(
        [],
        "XF86AudioPrev",
        lazy.spawn("/home/ervin/bin/mediactl.sh previous"),
        desc="Previous media",
    ),
    Key(
        [],
        "XF86AudioNext",
        lazy.spawn("/home/ervin/bin/mediactl.sh next"),
        desc="Next media",
    ),
    Key(
        [],
        "XF86AudioMicMute",
        lazy.spawn("/home/ervin/bin/mediactl.sh play-pause"),
        desc="Play/pause media",
    ),
    Key(
        [],
        "XF86AudioPlay",
        lazy.spawn("/home/ervin/bin/mediactl.sh play"),
        desc="Play/pause media",
    ),
    Key(
        [],
        "XF86AudioPause",
        lazy.spawn("/home/ervin/bin/mediactl.sh pause"),
        desc="Play/pause media",
    ),
    Key(
        [],
        "XF86MonBrightnessUp",
        lazy.spawn("/home/ervin/bin/brightnessctl.sh up"),
        desc="Brightness up by 10%",
    ),
    Key(
        [],
        "XF86MonBrightnessDown",
        lazy.spawn("/home/ervin/bin/brightnessctl.sh down"),
        desc="Brightness down by 10%",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "space",
        lazy.widget["keyboardlayout"].next_keyboard(),
        desc="Cycle through available keyboard layouts",
    ),
    # Key(
    #     [settings["keymaps"]["mod"]],
    #     "space",
    #     lazy.spawn(["ibus", "engine", "shin"]),
    #     desc="Activate shin",
    # ),
    Key(
        [settings["keymaps"]["alt"]],
        "F5",
        groupbox_disable_drag(),
        desc="Disable GroupBox widget group drag",
    ),
]
