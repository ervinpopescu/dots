import os

import json5
from modules.path import config_path
from modules.settings import settings

with open(os.path.join(config_path, "json", "matches.json"), "r") as f:
    data = json5.loads(f.read())

d = {
    settings["group_names"][i]: data[str(i)]
    for i in range(len(settings["group_names"]))
}
