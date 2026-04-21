from .groups import groups
from .hooks import apps as apps_hooks
from .hooks import misc as misc_hooks
from .hooks import qalttab as qalttab_hooks
from .hooks import window_rules as window_rules_hooks
from .idle import idle_inhibitors, idle_timers
from .keys import keys
from .layouts import floating_layout, layouts
from .mouse import mouse
from .screens import generate_screens

__all__ = [
    "apps_hooks",
    "floating_layout",
    "groups",
    "idle_inhibitors",
    "idle_timers",
    "keys",
    "layouts",
    "misc_hooks",
    "mouse",
    "generate_screens",
    "window_rules_hooks",
    "qalttab_hooks",
]
