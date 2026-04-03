#!/bin/python
import subprocess
import time

ac_power_online_filename = "/sys/class/power_supply/ACAD/online"
battery_percentage_filename = "/sys/class/power_supply/BAT1/capacity"


def notify_send(notification, urgency, id):
    subprocess.run(
        f"notify-send -a batteryNotification -i /usr/share/icons/Papirus/24x24/panel/battery-low.svg -u {urgency} -r {id}".split()
        + [notification]
    )


notification_id = "636223"

while True:
    with open(ac_power_online_filename, "r") as f:
        AC_online = int(f.read()) == 1
    with open(battery_percentage_filename, "r") as f:
        percentage = int(f.read())
    if percentage < 10:
        if not AC_online:
            notify_send(
                notification="charge your laptop!",
                urgency="critical",
                id=notification_id,
            )
    time.sleep(10)
