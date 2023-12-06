import asyncio
import contextlib
import os
import signal
import subprocess
from time import sleep

import json5
import psutil
from libqtile import hook, qtile
from libqtile.backend.base import Window
from libqtile.core.manager import Qtile

from modules.matches import d
from modules.path import config_path
from modules.settings import settings

qtile: Qtile

with open(os.path.join(config_path, "json", "window_rules.json"), "r") as f:
    rules: dict = json5.loads(f.read())


def check_if_process_running(process_name):
    """
    Check if there is any running process that contains the given name processName.
    """
    # Iterate over the all the running process
    for proc in psutil.process_iter():
        with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Check if process name contains the given name string.
            if process_name.lower() in proc.name().lower():
                return True
    return False


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


# @hook.subscribe.client_new
# @hook.subscribe.client_focus
# @hook.subscribe.client_managed
# def bring_plank_to_front(client: Window):
#     for window in qtile.windows_map.values():
#         if window.name == "plank":
#             window.bring_to_front()

# @hook.subscribe.client_new
# async def move_client(client):
#     await asyncio.sleep(0.1)
#     if client.window.get_wm_class()[0] == "spotify":
# client.togroup("media", switch_group=True, toggle=False)


@hook.subscribe.client_new
def assign_app_to_group(client: Window):
    try:
        wm_class = client.window.get_wm_class()[0]
    except Exception:
        wm_class = None
    for i in range(len(d)):
        if wm_class in list(d.values())[i]:
            group = list(d.keys())[i]
            client.togroup(group, toggle=False)
            client.group.toscreen(toggle=False)


@hook.subscribe.client_new
def resize_and_move_client(client: Window):
    try:
        wm_class = client.window.get_wm_class()[0]
    except Exception:
        wm_class = None
    try:
        role = client.get_wm_role()
    except Exception:
        role = None

    for key, win in rules.items():
        if key in [wm_class, role]:
            if "set_position_floating" in win and key == "gsimplecal":
                client.set_position_floating(
                    x=2880 - win["w"] - settings["margin_size"] - 5,
                    y=settings["bar_height"] + 2 * settings["margin_size"],
                )

            if "set_size_floating" in win:
                if key == "blueman-manager":
                    sleep(3)
                client.set_size_floating(w=win["w"], h=win["h"])

            if "toggle_floating" in win:
                client.toggle_floating()

            if "center" in win:
                client.center()

            if "keep_above" in win:
                client.keep_above()

    if "Musializer" in [wm_class, role]:
        # win = client.window
        # desktop_atom = win.conn.atoms["_NET_WM_WINDOW_TYPE_DESKTOP"]
        # win.set_property("_NET_WM_WINDOW_TYPE", [desktop_atom])
        # state_atoms = [
        #     win.conn.atoms[i]
        #     for i in [
        #         "_NET_WM_STATE_STICKY",
        #         "_NET_WM_STATE_SKIP_TASKBAR",
        #         "_NET_WM_STATE_SKIP_PAGER",
        #         "_NET_WM_STATE_FULLSCREEN",
        #     ]
        # ]
        # prev_state = set(win.get_property("_NET_WM_STATE", "ATOM", unpack=int))
        # client.set_wm_state(prev_state, state_atoms)
        client.toggle_fullscreen()
        client.keep_below(enable=True)
        client.change_layer()


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

# plank_instance = None

# @hook.subscribe.client_managed
# def register_and_bring_to_front_plank_instance(client):
#     global plank_instance
#     if client.name == "plank":
#         plank_instance = client
#     elif plank_instance is not None:
#         plank_instance.client.configure(stackmode=StackMode.Above)

# @hook.subscribe.client_killed
# def unregister_plank_instance(client):
#     global plank_instance
#     if client.name == "plank":
#         plank_instance = None
