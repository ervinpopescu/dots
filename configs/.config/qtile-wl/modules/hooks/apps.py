import asyncio
import os
import signal
import subprocess

from libqtile import hook
from libqtile.core.manager import Qtile
from libqtile.log_utils import logger
from libqtile.utils import create_task

from modules.settings import config_path

qtile: Qtile


@hook.subscribe.startup_once
def autostart():
    create_task(run_autostart()).add_done_callback(autostart_done)  # type: ignore
    # subprocess.call(
    #     [os.path.expanduser("~/bin/birthday-notification.sh")],
    #     stdout=subprocess.DEVNULL,
    #     stderr=subprocess.STDOUT,
    # )


async def run_autostart():
    autostart = os.path.expanduser("~/bin/autostart-wl.sh")
    with open(os.path.join(config_path, "autostart.log"), "w") as autostart_log_file:
        proc = await asyncio.create_subprocess_exec(
            autostart,
            stdout=autostart_log_file,
            # stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        return_code = await proc.wait()
        return return_code


def autostart_done(return_code):
    logger.info(f"Autostart finished with return code {return_code}")


@hook.subscribe.shutdown
def kill_all_autostarted_programs():
    with open("/tmp/autostart-wl_pids", "r") as pids_file:
        pids = pids_file.readlines()
        if not pids:
            for pid in pids:
                os.kill(int(pid), signal.SIGKILL)
