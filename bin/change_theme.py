#!/bin/python

import json
import subprocess
from datetime import datetime
from time import sleep

while True:
    with open("/tmp/sunrise", "r") as f:
        sunrise = f.read().strip()
    with open("/tmp/sunset", "r") as f:
        sunset = f.read().strip()
    with open("/home/ervin/.config/qtile/config.json") as f:
        config = json.load(f)
    with open("/home/ervin/.config/qtile/themes.json") as f:
        themes = json.load(f)
    now = datetime.now().strftime("%H:%M:%S")
    if now > sunset or now < sunrise:
        if config["theme"] != themes["night"]:
            subprocess.call(f'qchanger.py -t {themes["night"]}'.split())
    else:
        if config["theme"] != themes["day"]:
            subprocess.call(f'qchanger.py -t {themes["day"]}'.split())
    sleep(60)
