from libqtile import qtile
from libqtile.config import Key
from libqtile.lazy import lazy

from modules.hooks.qalttab import cycle_windows

from .apps import apps_keys
from .de import de_keys
from .layout_managing import layout_managing_keys
from .layouts import layouts_keys
from .qtile_stuff import qtile_keys
from .window_managing import window_managing_keys
from .windows_and_groups import windows_and_groups_keys

keys = []
keys.extend(windows_and_groups_keys)
keys.extend(layouts_keys)
keys.extend(layout_managing_keys)
keys.extend(window_managing_keys)
keys.extend(qtile_keys)
keys.extend(apps_keys)
keys.extend(de_keys)
# Add key bindings to switch VTs in Wayland.
# We can't check qtile.core.name in default config as it is loaded before qtile is started
# We therefore defer the check until the key binding is run by using .when(func=...)
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
keys.append(Key(["mod1"], "Tab", lazy.function(cycle_windows), desc="Cycle windows"))

__all__ = ["keys"]
