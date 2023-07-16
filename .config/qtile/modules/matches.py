import os

import json5

from modules.path import config_path
from modules.settings import group_names

with open(os.path.join(config_path, "json", "matches.json"), "r") as f:
    data = json5.loads(f.read())

d = {group_names[i]: data[str(i)] for i in range(len(group_names))}
