from libqtile.config import Click, Drag
from libqtile.lazy import lazy

# from extras.floating_window_snapping import move_snap_window
from modules.settings import settings

mouse = [
    Drag(
        [settings["keymaps"]["mod"]],
        "Button1",
        # move_snap_window(snap_dist=10),
        lazy.window.set_position(),
        start=lazy.window.get_position(),
    ),
    Drag(
        [settings["keymaps"]["mod"]],
        "Button3",
        lazy.window.set_size_floating(),
        start=lazy.window.get_size(),
        # warp_pointer=True,
    ),
    Click(
        [settings["keymaps"]["mod"]],
        "Button2",
        lazy.window.bring_to_front(),
    ),
    Click(
        [settings["keymaps"]["mod"]],
        "Button5",
        lazy.layout.grow_right().when(layout=["bsp", "columns"]),
        lazy.layout.grow().when(layout=["monadwide", "monadtall", "monadthreecol"]),
        lazy.layout.increase_ratio().when(layout="spiral"),
    ),
    Click(
        [settings["keymaps"]["mod"]],
        "Button4",
        lazy.layout.grow_left().when(layout=["bsp", "columns"]),
        lazy.layout.shrink().when(layout=["monadwide", "monadtall", "monadthreecol"]),
        lazy.layout.decrease_ratio().when(layout="spiral"),
    ),
]
