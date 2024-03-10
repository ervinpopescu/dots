#!/bin/python

import argparse
import contextlib
import os
import subprocess
import sys
from time import sleep

import psutil
from libqtile.command.client import InteractiveCommandClient


def dunstify(string):
    command = "dunstify -t 5000 -a orar -u normal -r 311213".split()
    subprocess.run(command + ["Error!", string])


def check_if_process_running(process_name):
    """
    Check if there is any running process that contains the given name processName.
    """
    # Iterate over the all the running process
    for proc in psutil.process_iter():
        with contextlib.suppress(
            psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess
        ):
            # Check if process name contains the given name string.
            if process_name.lower() in proc.name().lower():
                return True
    return False


def main():
    c = InteractiveCommandClient()
    parser = argparse.ArgumentParser(description="open Markdown preview in qt window")
    parser.add_argument(
        "url",
        default=None,
        help="url to open in qt window",
    )
    parser.add_argument(
        "-f",
        "--file",
        dest="file",
        default=None,
        help="file to open in qt window",
    )
    if check_if_process_running("qt_html.py"):
        subprocess.run(["pkill", "-9", "qt_html.py"])
    browser = f"qt_html.py {' '.join(sys.argv[1:])}"
    c.spawn(browser)
    c.group.setlayout("monadtall")
    sleep(1)
    c.group.focus_back()


if __name__ == "__main__":
    main()
