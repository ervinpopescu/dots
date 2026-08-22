import json
from os import path

from modules.settings import config_path, load_runtime_config


def load_theme():
    theme = load_runtime_config(config_path)["theme"]

    theme_file = path.join(config_path, "themes", f"{theme}.json")
    if not path.isfile(theme_file):
        raise FileNotFoundError(f'"{theme_file}" does not exist')

    try:
        with open(theme_file) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f'could not load theme "{theme}"') from error


if __name__ == "modules.theme":
    colors = load_theme()
