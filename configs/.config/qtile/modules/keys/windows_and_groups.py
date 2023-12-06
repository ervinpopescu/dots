import os

from libqtile.config import Key
from libqtile.lazy import lazy
from modules.functions import (
    switch_win_in_group,
    toggle_minimize_all,
    window_to_next_group,
    window_to_prev_group,
)
from modules.settings import settings

windows_and_groups_keys = [
    Key(
        [settings["cmds"]["mod"]],
        "Up",
        # lazy.group.next_window(),
        switch_win_in_group(),
        desc="Next window in group",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "Down",
        # lazy.group.prev_window(),
        switch_win_in_group(),
        desc="Previous window in group",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "Right",
        lazy.screen.next_group(skip_empty=True),
        desc="Next group (skip empty ones)",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "Left",
        lazy.screen.prev_group(skip_empty=True),
        desc="Previous group (skip empty ones)",
    ),
    Key(
        [settings["cmds"]["mod"], settings["cmds"]["alt"]],
        "Right",
        window_to_next_group(),
        desc="Send window to next group (not skipping empty ones)",
    ),
    Key(
        [settings["cmds"]["mod"], settings["cmds"]["alt"]],
        "Left",
        window_to_prev_group(),
        desc="Send window to previous group (not skipping empty ones)",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "grave",
        lazy.window.toggle_minimize(),
        desc="Minimize current window",
    ),
    Key(
        [settings["cmds"]["mod"], "shift"],
        "d",
        toggle_minimize_all(current_group=True),
        desc="Minimize all windows in current group",
    ),
    Key(
        [settings["cmds"]["mod"]],
        "d",
        toggle_minimize_all(current_group=False),
        desc="Minimize all windows in all groups",
    ),
]
