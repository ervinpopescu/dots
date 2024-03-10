#!/bin/python
import argparse
import contextlib
import json
import os
import pathlib
import shutil
import subprocess

import psutil
import pycritty
from libqtile.command.client import InteractiveCommandClient
from rofi import Rofi

c = InteractiveCommandClient()
qtile_path = pathlib.Path(c.qtile_info()["config_path"]).parent.resolve()
themes = ["catppuccin", "nord"]


def load_properties(filepath, sep="=", comment_char="#"):
    """
    Read the file passed as parameter as a properties file.
    """
    props = {}
    with open(filepath, "rt") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith(comment_char):
                key_value = stripped.split(sep)
                key = key_value[0].strip()
                value = sep.join(key_value[1:]).strip().strip('"')
                props[key] = value
    return props


def dunstify(string):
    subprocess.run(f"dunstify -a theme -u normal -r 342523 {string}".split())


def set_pycritty(theme):
    config = pycritty.Config()
    config.change_theme(theme)
    config.apply()


def set_qtile(theme):
    config = os.path.join(qtile_path, "json", "config.json")
    with open(config, "r") as f:
        config_json = json.load(f)
        config_json["theme"] = theme
    with open(config, "w") as f:
        json.dump(config_json, f, indent=4)
    c.reload_config()


def set_firefox(theme):
    firefox_theme_file = os.path.join(qtile_path, "firefox_themes", "firefox_theme.json")
    theme_file = os.path.join(qtile_path, "firefox_themes", "themes", f"{theme}.json")
    shutil.copy(theme_file, firefox_theme_file)


def set_vscode(theme):
    settings_file = os.path.join(
        os.path.expanduser("~"), ".config", "Code", "User", "settings.json"
    )
    with open(settings_file, "r") as f:
        settings = json.load(f)

    match theme:
        case "nord":
            settings["workbench.colorTheme"] = "Nord"
        case "catppuccin":
            settings["workbench.colorTheme"] = "Catppuccin Mocha"

    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2)


def set_gtk(theme):
    settings_file = os.path.join(
        os.path.expanduser("~"), ".config", "xsettingsd", "xsettingsd.conf"
    )
    settings = load_properties(settings_file, sep=" ")

    match theme:
        case "nord":
            settings["Net/ThemeName"] = '"Nordic-darker"'
        case "catppuccin":
            settings["Net/ThemeName"] = '"Catppuccin-Mocha-Standard-Blue-dark"'

    with open(settings_file, "w") as f:
        for key, value in settings.items():
            f.write(f"{key} {value}\n")

    for proc in psutil.process_iter():
        if proc.name() == "xsettingsd":
            proc.kill()

    subprocess.Popen(
        "xsettingsd",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def set_rofi(theme):
    settings_file = os.path.join(os.path.expanduser("~"), ".config", "rofi", "config.rasi")
    with open(settings_file, "r") as f:
        settings = f.readlines()

    theme_line = []
    theme_line_index = None

    for i in range(len(settings)):
        if "@theme" in settings[i]:
            theme_line = settings[i].strip().split()
            theme_line_index = i

    theme_line[1] = f'"{theme}"\n'
    theme_line = " ".join(theme_line)
    settings[theme_line_index] = theme_line

    with open(settings_file, "w") as f:
        f.writelines(settings)


def set_neovim(theme):
    colorscheme_file = os.path.join(
        os.path.expanduser("~"),
        ".config",
        "nvim",
        "lua",
        "plugins",
        "colorscheme.lua",
    )
    with open(colorscheme_file, "w") as f:
        f.writelines(
            [
                'return { "LazyVim/LazyVim", opts = {',
                f'\tcolorscheme = "{theme}"',
                "} }",
            ]
        )


def set_all(theme):
    dunstify(theme)
    set_pycritty(theme)
    set_firefox(theme)
    set_vscode(theme)
    set_gtk(theme)
    set_rofi(theme)
    set_neovim(theme)
    set_qtile(theme)


def main():
    parser = argparse.ArgumentParser(
        prog="qchanger.py",
        description="Change OS theme",
    )
    parser.add_argument(
        "-t",
        "--theme",
        choices=themes,
        dest="theme",
    )
    args = parser.parse_args()
    if args.theme is not None:
        theme = args.theme
        set_all(theme)
    else:
        r = Rofi()
        index, key = r.select("Select theme", themes)
        theme = themes[index]
        if key == 0:
            set_all(theme)


if __name__ == "__main__":
    main()
