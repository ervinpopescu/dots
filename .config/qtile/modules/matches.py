import json
import os

from modules.settings import group_names

with open(os.path.dirname(os.path.realpath(__file__)) + "/" + "matches.json") as f:
    data = json.load(f)

d = dict()
for i in range(len(group_names)):
    d[group_names[i]] = data[str(i)]
