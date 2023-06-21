#!/bin/python

import argparse
import os
import subprocess
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
        try:
            # Check if process name contains the given name string.
            if process_name.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


c = InteractiveCommandClient()
parser = argparse.ArgumentParser(description="open Markdown preview in browser window")
parser.add_argument("url", action="store", help="url to open in browser window")
args = parser.parse_args()
if check_if_process_running("qt_html.py"):
    subprocess.run(["pkill", "-9", "qt_html.py"])
browser = "qt_html.py " + args.url
c.spawn(browser)
c.group.setlayout("monadtall")
sleep(1)
c.group.focus_back()
