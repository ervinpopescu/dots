import os
import signal
import subprocess

from libqtile import hook
from libqtile.core.manager import Qtile

from modules.settings import config_path

qtile: Qtile


@hook.subscribe.startup_once
def autostart():
    autostart = os.path.expanduser("~/bin/autostart-wl.sh")
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


@hook.subscribe.shutdown
def kill_all_autostarted_programs():
    with open("/tmp/autostart-wl_pids", "r") as pids_file:
        pids = pids_file.readlines()
        if not pids:
            for pid in pids:
                os.kill(int(pid), signal.SIGKILL)
