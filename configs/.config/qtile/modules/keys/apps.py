import os

from libqtile.config import Key, KeyChord
from libqtile.lazy import lazy

from modules.functions import suspend_toggle
from modules.settings import config_path, settings

apps_keys = [
    KeyChord(
        [settings["keymaps"]["mod"]],
        "s",
        [
            Key(
                [],
                "b",
                lazy.spawn("rfkill unblock bluetooth", shell=True),
                lazy.group["scratchpad"].dropdown_toggle("blueman"),
                desc="Open Bluetooth manager",
            ),
            Key(
                [],
                "k",
                lazy.group["scratchpad"].dropdown_toggle("keys"),
                desc="Open keybindings window",
            ),
            Key(
                [],
                "p",
                lazy.group["scratchpad"].dropdown_toggle("pavucontrol"),
                desc="Open PulseAudio Volume Control",
            ),
            Key([], "s", suspend_toggle(), desc="Toggle suspend"),
            Key(
                [],
                "t",
                lazy.group["scratchpad"].dropdown_toggle("term"),
                desc="Open terminal dropdown",
            ),
            Key(
                [],
                "f",
                lazy.group["scratchpad"].dropdown_toggle("files"),
                desc="Open nemo dropdown",
            ),
        ],
        name="settings",
        mode=False,
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "a",
        lazy.spawn(settings["cmds"]["menu"]),
        desc="Open rofi application menu",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "j",
        lazy.spawn(settings["cmds"]["emoji"]),
        desc="Open rofi emoji picker",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "w",
        lazy.spawn(settings["cmds"]["wallpaper"]),
        desc="Open rofi wallpaper picker",
    ),
    # Key(
    #     [settings["keymaps"]["mod"]],
    #     "b",
    #     lazy.spawn("/home/ervin/bin/bookmarks.py"),
    #     desc="Open bookmarks",
    # ),
    Key(
        [settings["keymaps"]["mod"]],
        "c",
        lazy.spawn("/home/ervin/.config/conky/start_qtile.sh -n"),
        desc="Open conky",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "f",
        lazy.spawn("nemo"),
        desc="Open GUI file manager (nemo)",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "m",
        lazy.spawn("/home/ervin/bin/start-spotify.py"),
        desc="Start Spotify (and/or GLava)",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "o",
        lazy.spawn("alacritty -e zsh -c lf"),
        desc="Open TUI file manager (lf)",
    ),
    # Key(
    #     [settings["keymaps"]["mod"]],
    #     "p",
    #     lazy.spawn("nwggrid -b 1e1e2eef -f -n 32"),
    #     desc="Open nwggrid application menu",
    # ),
    Key(
        [settings["keymaps"]["mod"]],
        "t",
        lazy.group["scratchpad"].dropdown_toggle("term"),
        desc="Toggle terminal scratchpad",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "u",
        lazy.spawn(settings["cmds"]["update"]),
        desc="Update system",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "x",
        lazy.spawn(settings["cmds"]["nwgbar"]),
        desc="Open powermenu (nwgbar)",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "z",
        lazy.spawn("firefox"),
        desc="Open Firefox",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "Return",
        lazy.spawn(settings["cmds"]["terminal"]),
        desc=f"Open {settings['cmds']['terminal']}",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "slash",
        lazy.spawn("rofi -modi ask-totoro:ask-totoro -show ask-totoro".split()),
        desc="Wolfram Alpha API requester",
    ),
    Key(
        [settings["keymaps"]["mod"]],
        "h",
        lazy.group["scratchpad"].dropdown_toggle("htop"),
        desc="Open htop",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "i",
        lazy.spawn("/home/ervin/bin/bookmarkthis.py"),
        desc="Add bookmark",
    ),
    Key(
        [settings["keymaps"]["alt"], "shift"],
        "s",
        lazy.spawn("flameshot gui"),
        desc="Open flameshot",
    ),
    Key(
        [settings["keymaps"]["mod"], "shift"],
        "t",
        lazy.spawn(os.path.join(config_path, "scripts", "qchanger.py")),
        desc="Change theme",
    ),
]
