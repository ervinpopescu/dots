import os

from libqtile.config import Key
from libqtile.lazy import lazy
from modules.path import config_path
from modules.settings import settings

apps_keys = [
    Key(
        [settings["cmds"]["mod"]],
        "a",
        lazy.spawn(settings["cmds"]["menu"]),
        desc="Open rofi application menu",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "j",
        lazy.spawn(settings["cmds"]["emoji"]),
        desc="Open rofi emoji picker",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "b",
        lazy.spawn("/home/ervin/bin/bookmarks.py"),
        desc="Open bookmarks",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "c",
        lazy.spawn("/home/ervin/.config/conky/start_qtile.sh -n"),
        desc="Open conky",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "l",
        lazy.spawn("/home/ervin/bin/licenta.py"),
        desc="Start working on thesis",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "f",
        lazy.spawn("nemo"),
        desc="Open GUI file manager (nemo)",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "i",
        lazy.spawn("/home/ervin/bin/orar.py"),
        desc="Open schedule",
    ),
    # Key(
    #     [settings["cmds"]["mod"]],
    #     "j",
    #     lazy.group["scratchpad"].dropdown_toggle("transmission"),
    #     desc="Open transmission",
    # ),
    Key(
        [settings["cmds"]["mod"]],
        "k",
        lazy.group["scratchpad"].dropdown_toggle("keys"),
        desc="Open keybindings window",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "l",
        lazy.spawn("betterlockscreen -l dimblur --span"),
        desc="Lock screen",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "m",
        lazy.spawn("/home/ervin/bin/start-spotify.py"),
        desc="Start Spotify (and/or GLava)",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "o",
        lazy.spawn("alacritty -e zsh -c lf"),
        desc="Open TUI file manager (lf)",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "p",
        lazy.spawn("nwggrid -b 1e1e2eef -f -n 32"),
        desc="Open nwggrid application menu",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "t",
        lazy.group["scratchpad"].dropdown_toggle("term"),
        desc="Toggle terminal scratchpad",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "u",
        lazy.spawn(settings["cmds"]["update"]),
        desc="Update system",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "x",
        lazy.spawn(settings["cmds"]["nwgbar"]),
        desc="Open powermenu (nwgbar)",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "z",
        lazy.spawn("firefox"),
        desc="Open Firefox",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "Return",
        lazy.spawn(settings["cmds"]["terminal"]),
        desc=f"Open {settings['cmds']['terminal']}",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "slash",
        lazy.spawn("rofi -modi ask-totoro:ask-totoro -show ask-totoro".split()),
        desc="Wolfram Alpha API requester",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "h",
        lazy.group["scratchpad"].dropdown_toggle("htop"),
        desc="Open htop",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "i",
        lazy.spawn("/home/ervin/bin/bookmarkthis.py"),
        desc="Add bookmark",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "s",
        lazy.spawn("flameshot screen -p /home/ervin/Pictures"),
        desc="Take full screenshot",
    ),
    Key(
        [settings["cmds"]["alt"], "shift"],
        "s",
        lazy.spawn("flameshot gui"),
        desc="Open flameshot",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "t",
        lazy.spawn(os.path.join(config_path, "scripts", "qchanger.py")),
        desc="Change theme",
    ),
]
