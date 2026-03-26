import os

from libqtile.config import IdleInhibitor, IdleTimer, Match  # type: ignore
from libqtile.lazy import lazy

from .settings import settings

idle_timers = [
    IdleTimer(300, lazy.spawn(os.path.expandvars("$CARGO_HOME/bin/dpms-off"))),
    IdleTimer(301, lazy.spawn(settings.cmds.lock)),
    IdleTimer(330, lazy.spawn("systemctl suspend")),
]

idle_inhibitors = [
    IdleInhibitor(match=Match(wm_class="vlc"), when="fullscreen"),
    IdleInhibitor(match=Match(wm_class="firefox"), when="fullscreen"),
]
