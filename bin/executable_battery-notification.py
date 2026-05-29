#!/usr/bin/env python3
import subprocess
import time
import sys
from pathlib import Path

# Constants
POWER_SUPPLY_DIR = Path("/sys/class/power_supply")
NOTIFICATION_ID = "636223"
CHECK_INTERVAL = 30  # Seconds


def find_power_paths():
    """Dynamically find AC and Battery paths."""
    ac_path = None
    bat_path = None

    if not POWER_SUPPLY_DIR.exists():
        return None, None

    for p in POWER_SUPPLY_DIR.iterdir():
        if "AC" in p.name:
            ac_path = p / "online"
        elif "BAT" in p.name:
            # Use the first battery found
            if bat_path is None:
                bat_path = p / "capacity"
    
    return ac_path, bat_path


def dunstify(notification, urgency="normal", msg_id=NOTIFICATION_ID):
    """Send a notification using dunstify."""
    cmd = [
        "dunstify",
        "-a", "batteryNotification",
        "-I", "/usr/share/icons/Papirus/24x24/panel/battery-low.svg",
        "-u", urgency,
        "-r", msg_id,
        notification
    ]
    try:
        subprocess.run(cmd, check=False, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("Error: dunstify command not found.", file=sys.stderr)


def main():
    ac_path, bat_path = find_power_paths()

    if not ac_path or not bat_path:
        # If we can't find the paths, we can't monitor.
        # This allows the script to fail fast rather than crash later.
        print(f"Error: Could not find AC or Battery paths in {POWER_SUPPLY_DIR}", file=sys.stderr)
        sys.exit(1)

    while True:
        try:
            # Read current state
            ac_online = False
            if ac_path.exists():
                ac_content = ac_path.read_text().strip()
                ac_online = (int(ac_content) == 1)
            
            percentage = 0
            if bat_path.exists():
                bat_content = bat_path.read_text().strip()
                percentage = int(bat_content)

            if percentage < 10:
                if ac_online:
                    # Clear the warning if plugged in
                    try:
                        subprocess.run(["dunstify", "-C", NOTIFICATION_ID], check=False, stderr=subprocess.DEVNULL)
                    except FileNotFoundError:
                        pass
                else:
                    dunstify(
                        notification="charge your laptop!",
                        urgency="critical",
                        msg_id=NOTIFICATION_ID,
                    )
        except ValueError:
             # Handle cases where file read might return partial/empty content temporarily
             pass
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
