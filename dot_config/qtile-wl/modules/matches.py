import os

import json5

from modules.settings import config_path, settings

with open(os.path.join(config_path, "json", "matches.json"), "r") as f:
    data = json5.loads(f.read())

matches = {
    list(settings.groups.keys())[i]: data[str(i)]  # type: ignore
    for i in range(len(settings.groups))
}
