import asyncio
import contextlib
import os
import signal
import subprocess
from time import sleep

import json5
from libqtile import hook, qtile
from libqtile.backend.base import Window
from libqtile.core.manager import Qtile
from modules.functions import check_if_process_running
from modules.matches import d, matches
from modules.path import config_path
from modules.settings import config_path, settings

qtile: Qtile

with open(os.path.join(config_path, "json", "window_rules.json"), "r") as f:
    rules: dict = json5.loads(f.read())


@hook.subscribe.startup_once
async def autostart():
    autostart = os.path.expanduser("~/bin/autostart.sh")
    with open(os.path.join(config_path, "autostart.log"), "w") as autostart_log_file:
        subprocess.call(
            [autostart],
            stdout=autostart_log_file,
            # stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
    await asyncio.sleep(10)
    subprocess.call(
        [os.path.expanduser("~/bin/birthday-notification.sh")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    await asyncio.sleep(10)
    for window in qtile.windows_map.values():
        if window.name == "plank":
            window.keep_above()


# @hook.subscribe.screen_change
# def reload(event):
#     qtile.reload_config()


@hook.subscribe.screens_reconfigured
async def change_wallpaper():
    with open(os.path.expanduser("~/.local/share/wallpaper/log")) as f:
        path = f.readlines()[0].split(" ")[-1]
    subprocess.call(f"run_wall.sh {path} all".split())


@hook.subscribe.client_new
@hook.subscribe.client_managed
def resize_and_move_client(client: Window):
    wm_class = client.window.get_wm_class()
    if wm_class:
        wm_class = wm_class[0]
    else:
        wm_class = None
    role = client.get_wm_role()
    if not role:
        role = None
    name = client.name
    if not name:
        name = None

    for group, wm_classes in matches.items():
        if wm_class in wm_classes:
            client.togroup(group)
            client.group.toscreen(toggle=False)
            return

    for key, win in rules.items():
        if key in [wm_class, role, name]:
            if "set_position_floating" in win and key == "gsimplecal":
                client.set_position_floating(
                    x=qtile.core.get_screen_info()[0][2] - win["w"] - settings["margin_size"] - 5,
                    y=settings["bar_height"] + 2 * settings["margin_size"],
                )
                return

            if "set_size_floating" in win:
                if key == "blueman-manager":
                    sleep(3)
                client.set_size_floating(w=win["w"], h=win["h"])
                return

            if "toggle_floating" in win:
                client.toggle_floating()
                return

            if "center" in win:
                client.center()
                return

            if "keep_above" in win:
                client.keep_above()
                return


@hook.subscribe.client_killed
def switch_group(client):
    with contextlib.suppress(AttributeError):
        num_windows_in_group = len(client.group.info()["windows"])
        if num_windows_in_group == 0:
            qtile.current_screen.toggle_group(qtile.current_screen.previous_group)


@hook.subscribe.shutdown
def kill_all_autostarted_programs():
    with open("/tmp/autostart_pids", "r") as pids_file:
        pids = pids_file.readlines()
        if not pids:
            for pid in pids:
                os.kill(int(pid), signal.SIGKILL)
    if check_if_process_running("plank"):
        for win in qtile.windows_map.values():
            if win.name == "plank":
                os.kill(int(win.eval("self.window.get_net_wm_pid()")[1]), signal.SIGKILL)


# noswallow = ["min", "Navigator", "vlc", "qtilekeys.py", "Alacritty"]

# @hook.subscribe.client_new
# def swallow(client):
#     if qtile.current_layout.name != "max":
#         try:
#             wm_class = client.window.get_wm_class()[0]
#         except Exception:
#             wm_class = None
#         if wm_class not in noswallow:
#             pid = client.window.get_net_wm_pid()
#             ppid = psutil.Process(pid).ppid()
#             cpids = {c.window.get_net_wm_pid(): wid for wid, c in qtile.windows_map.items()}
#             for i in range(5):
#                 if not ppid:
#                     return
#                 if ppid in cpids:
#                     parent = qtile.windows_map.get(cpids[ppid])
#                     parent.minimized = True
#                     client.parent = parent
#                     return
#                 ppid = psutil.Process(ppid).ppid()

# @hook.subscribe.client_killed
# def unswallow(client):
#     if hasattr(client, "parent"):
#         client.parent.minimized = False
