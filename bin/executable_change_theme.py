#!/usr/bin/env python3

import json
import subprocess
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from time import sleep

def main():
    qchanger = shutil.which("qchanger.py")
    if not qchanger:
        # Try relative to script or home/bin
        qchanger = str(Path.home() / "bin" / "qchanger.py")
        if not Path(qchanger).exists():
             print("Error: qchanger.py not found in PATH or ~/bin.", file=sys.stderr)
             sys.exit(1)

    qtile_config = Path.home() / ".config" / "qtile" / "config.json"
    qtile_themes = Path.home() / ".config" / "qtile" / "themes.json"

    while True:
        try:
            # Handle sunrise/sunset files
            sunrise = "07:00:00"
            sunset = "18:00:00"
            
            if os.path.exists("/tmp/sunrise"):
                with open("/tmp/sunrise", "r") as f:
                    sunrise = f.read().strip()
            
            if os.path.exists("/tmp/sunset"):
                with open("/tmp/sunset", "r") as f:
                    sunset = f.read().strip()

            if not qtile_config.exists() or not qtile_themes.exists():
                print("Error: Qtile theme configs not found.", file=sys.stderr)
                sleep(300)
                continue

            with open(qtile_config, "r") as f:
                config = json.load(f)
            with open(qtile_themes, "r") as f:
                themes = json.load(f)
            
            now = datetime.now().strftime("%H:%M:%S")
            
            target_theme = None
            if now > sunset or now < sunrise:
                if config.get("theme") != themes.get("night"):
                    target_theme = themes.get("night")
            elif config.get("theme") != themes.get("day"):
                target_theme = themes.get("day")

            if target_theme:
                subprocess.run([qchanger, "-t", target_theme], check=False)
                
        except Exception as e:
            print(f"Theme switcher error: {e}", file=sys.stderr)

        sleep(60)

if __name__ == "__main__":
    main()
