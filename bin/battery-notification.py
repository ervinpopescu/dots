#!/bin/python
import subprocess
import time

ac_power_online_filename = "/sys/class/power_supply/ACAD/online"
battery_percentage_filename = "/sys/class/power_supply/BAT1/capacity"


def dunstify(notification, urgency, id):
    subprocess.run(
        f"dunstify -a batteryNotification -I /usr/share/icons/Papirus/24x24/panel/battery-low.svg -u {urgency} -r {id}".split()
        + [notification]
    )

notification_id = "636223"

while True:
    with open(ac_power_online_filename, "r") as f:
        AC_online = int(f.read()) == 1
    with open(battery_percentage_filename, "r") as f:
        percentage = int(f.read())
    if percentage < 10:
        if AC_online is False:
            dunstify(notification="charge your laptop!", urgency="critical", id=notification_id)
        elif AC_online is True:
            subprocess.run(f"dunstify -C {notification_id}".split())
            # playsound("/usr/share/sounds/freedesktop/stereo/power-plug.oga")
    time.sleep(10)
