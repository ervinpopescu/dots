import json
from os import path

from modules.path import config_path


def load_theme():
    theme = "catppuccin"

    config = path.join(config_path, "json", "config.json")
    if path.isfile(config):
        with open(config) as f:
            theme = json.load(f)["theme"]
    else:
        with open(config, "w") as f:
            f.write(f'{{"theme": "{theme}"}}\n')

    theme_file = path.join(config_path, "themes", f"{theme}.json")
    if not path.isfile(theme_file):
        raise FileNotFoundError(f'"{theme_file}" does not exist')

    with open(path.join(theme_file)) as f:
        return json.load(f)


if __name__ == "modules.theme":
    colors = load_theme()
