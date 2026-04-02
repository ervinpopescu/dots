import os
import subprocess

from libqtile import hook, qtile
from libqtile.utils import send_notification


@hook.subscribe.screen_change
def change_wallpaper(event):
    with open(os.path.expanduser("~/.local/share/wallpaper/log")) as f:
        path = f.readlines()
    if path is not None and len(path) != 0:
        subprocess.call(f"run_wall_wl.sh {path} all".split())
    else:
        subprocess.call("run_wall_wl.sh rand all".split())
    n_screens = len(qtile.get_screens())
    if n_screens == 3 or n_screens == 1:
        qtile.reconfigure_screens()
        qtile.reload_config()


@hook.subscribe.client_urgent_hint_changed
def client_urgency_change(client):
    send_notification("qtile", f"{client.name} has changed its urgency state")
