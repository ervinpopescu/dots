import os
import signal
import subprocess

from libqtile import hook, qtile
from libqtile.core.manager import Qtile

from modules.functions import check_if_process_running
from modules.settings import config_path

qtile: Qtile

@hook.subscribe.startup_once
def autostart():
    qtile.info()
    autostart = os.path.expanduser("~/bin/autostart.sh")
    with open(os.path.join(config_path, "autostart.log"), "w") as autostart_log_file:
        subprocess.call(
            [autostart],
            stdout=autostart_log_file,
            # stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
    subprocess.call(
        [os.path.expanduser("~/bin/birthday-notification.sh")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    for window in qtile.windows_map.values():
        if window.name == "plank":
            window.keep_above()

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
