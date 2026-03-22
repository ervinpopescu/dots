import os

from libqtile.config import IdleTimer
from libqtile.lazy import lazy

idle_timers = [
    IdleTimer(15, lazy.spawn(os.path.expanduser("~/.cargo/bin/dpms-off"))),
    IdleTimer(30, lazy.spawn("systemctl suspend")),
]
