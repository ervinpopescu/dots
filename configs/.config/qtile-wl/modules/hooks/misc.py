import contextlib
import os
import subprocess

from libqtile import hook, qtile
from libqtile.core.manager import Qtile

qtile: Qtile

# @hook.subscribe.screen_change
# def screen_change(event):
#     qtile.reconfigure_screens()
#     qtile.reconfigure_screens()


@hook.subscribe.screens_reconfigured
async def change_wallpaper():
    with open(os.path.expanduser("~/.local/share/wallpaper/log")) as f:
        path = f.readlines()
    if path is not None or path.len() != 0:
        subprocess.call(f"run_wall-wl.sh {path} all".split())
    else:
        subprocess.call("run_wall-wl.sh rand all".split())


@hook.subscribe.client_killed
def switch_group(client):
    with contextlib.suppress(AttributeError):
        num_windows_in_group = len(client.group.info()["windows"])
        if num_windows_in_group == 0:
            qtile.current_screen.toggle_group(qtile.current_screen.previous_group)  # type: ignore


# @hook.subscribe.startup
# def set_properties():
#     for screen in qtile.screens:
#         screen.bottom.window.window.set_property("ROUNDED_CORNERS_EXCLUDE", 1, "CARDINAL", 32)
#     for p in psutil.process_iter():
#         if p.name() == "picom":
#             p.send_signal(signal.SIGUSR1)
