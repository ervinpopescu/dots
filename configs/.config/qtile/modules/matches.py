import os

import json5

from modules.settings import config_path, settings

with open(os.path.join(config_path, "json", "matches.json"), "r") as f:
    data = json5.loads(f.read())

matches = {settings["group_names"][i]: data[str(i)] for i in range(len(settings["group_names"]))}
