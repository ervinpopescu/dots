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


__all__ = ["keys"]
