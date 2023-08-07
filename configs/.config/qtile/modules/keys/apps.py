import os

from libqtile.config import Key
from libqtile.lazy import lazy

from modules.path import config_path
from modules.settings import cmds

apps_keys = [
    Key(
        [cmds["mod"]],
        "a",
        lazy.spawn(cmds["menu"]),
        desc="Open rofi application menu",
    ),
    Key(
        [cmds["mod"], "shift"],
        "j",
        lazy.spawn(cmds["emoji"]),
        desc="Open rofi emoji picker",
    ),
    Key(
        [cmds["mod"]],
        "b",
        lazy.spawn("/home/ervin/bin/bookmarks.py"),
        desc="Open bookmarks",
    ),
    Key(
        [cmds["mod"]],
        "c",
        lazy.spawn("/home/ervin/.config/conky/start_qtile.sh -n"),
        desc="Open conky",
    ),
    Key(
        [cmds["mod"], "shift"],
        "l",
        lazy.spawn("/home/ervin/bin/licenta.py"),
        desc="Start working on thesis",
    ),
    Key(
        [cmds["mod"]],
        "f",
        lazy.spawn("nemo"),
        desc="Open GUI file manager (nemo)",
    ),
    Key(
        [cmds["mod"]],
        "i",
        lazy.spawn("/home/ervin/bin/orar.py"),
        desc="Open schedule",
    ),
    # Key(
    #     [cmds["mod"]],
    #     "j",
    #     lazy.group["scratchpad"].dropdown_toggle("transmission"),
    #     desc="Open transmission",
    # ),
    Key(
        [cmds["mod"]],
        "k",
        lazy.group["scratchpad"].dropdown_toggle("keys"),
        desc="Open keybindings window",
    ),
    Key(
        [cmds["mod"]],
        "l",
        lazy.spawn("betterlockscreen -l dimblur --span"),
        desc="Lock screen",
    ),
    Key(
        [cmds["mod"]],
        "m",
        lazy.spawn("/home/ervin/bin/start-spotify.py"),
        desc="Start Spotify (and/or GLava)",
    ),
    Key(
        [cmds["mod"]],
        "o",
        lazy.spawn("alacritty -e zsh -c lf"),
        desc="Open TUI file manager (lf)",
    ),
    Key(
        [cmds["mod"]],
        "p",
        lazy.spawn("nwggrid -b 1e1e2eef -f -n 32"),
        desc="Open nwggrid application menu",
    ),
    Key(
        [cmds["mod"]],
        "t",
        lazy.group["scratchpad"].dropdown_toggle("term"),
        desc="Toggle terminal scratchpad",
    ),
    Key(
        [cmds["mod"]],
        "u",
        lazy.spawn(cmds["update"]),
        desc="Update system",
    ),
    Key(
        [cmds["mod"]],
        "x",
        lazy.spawn(cmds["nwgbar"]),
        desc="Open powermenu (nwgbar)",
    ),
    Key(
        [cmds["mod"]],
        "z",
        lazy.spawn("firefox"),
        desc="Open Firefox",
    ),
    Key(
        [cmds["mod"]],
        "Return",
        lazy.spawn(cmds["terminal"]),
        desc=f"Open {cmds['terminal']}",
    ),
    Key(
        [cmds["mod"]],
        "slash",
        lazy.spawn("rofi -modi ask-totoro:ask-totoro -show ask-totoro".split()),
        desc="Wolfram Alpha API requester",
    ),
    Key(
        [cmds["mod"]],
        "h",
        lazy.group["scratchpad"].dropdown_toggle("htop"),
        desc="Open htop",
    ),
    Key(
        [cmds["mod"], "shift"],
        "i",
        lazy.spawn("/home/ervin/bin/bookmarkthis.py"),
        desc="Add bookmark",
    ),
    Key(
        [cmds["mod"], "shift"],
        "s",
        lazy.spawn("flameshot screen -p /home/ervin/Pictures"),
        desc="Take full screenshot",
    ),
    Key(
        [cmds["alt"], "shift"],
        "s",
        lazy.spawn("flameshot gui"),
        desc="Open flameshot",
    ),
    Key(
        [cmds["mod"], "shift"],
        "t",
        lazy.spawn(os.path.join(config_path, "scripts", "qchanger.py")),
        desc="Change theme",
    ),
]
