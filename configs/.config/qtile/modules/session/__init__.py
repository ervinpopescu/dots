import json
import psutil
import os
from libqtile import qtile
from libqtile.log_utils import logger
from modules.path import config_path

excluded_apps = ["plank"]

class Session:
    def __init__(self):
        self.apps: list[dict[int, str]] = []
        self.save_path = os.path.join(config_path, "json", "session.json")
        if not os.path.exists(self.save_path):
            self.from_windows()
        else:
            self.restore()

    def add_app(self, wid: int, exe: str):
        if not (any(app["wid"] == wid for app in self.apps) or any(i in exe for i in excluded_apps) or qtile.windows_map[wid].group.name == "scratchpad"):
            logger.info("Adding %s to session", exe)
            self.apps.append({"wid": wid, "exe": exe})
        else:
            logger.info("NOT adding excluded app %s to session", exe)
        self.log()

    def remove_app(self, wid: int):
        for i in range(len(self.apps)):
            if self.apps[i]["wid"] == wid:
                exe = next((app["exe"] for app in self.apps if app["wid"] == wid), None)
                logger.info("Removing %s from session", exe)
                del self.apps[i]
                break
        self.log()

    def save(self):
        with open(self.save_path, "w") as f:
            json.dump(self.apps, f)
        apps = [app["exe"] for app in self.apps]
        logger.info("Saving session with apps: %s", ",".join(apps))

    def restore(self):
        with open(self.save_path, "r") as f:
            self.apps = json.load(f)

    def clear(self):
        self.log()
        logger.info("Clearing session")
        self.apps = []
        self.log()

    def from_windows(self):
        self.log()
        logger.info("Setting session from current windows")
        windows = qtile.windows()
        if windows:
            for window in windows:
                wid = window["id"]
                exe = psutil.Process(int(qtile.windows_map[wid].get_pid())).exe()
                self.add_app(
                    wid=wid,
                    exe=exe,
                )
        self.log()

    def log(self):
        logger.info("Session: %s", self.apps)
