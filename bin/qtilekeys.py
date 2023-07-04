#!/usr/bin/env python3

import argparse
import os
import pathlib
import re

import gi
import jsonpickle

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from libqtile.command.client import InteractiveCommandClient
from markdownTable import markdownTable

c = InteractiveCommandClient()
qtile_path = pathlib.Path(c.qtile_info()["config_path"]).parent.resolve()

# with open(os.path.join(qtile_path, "keys.pickle"), "rb") as f:
#     keys = pickle.load(f)
with open(os.path.join(qtile_path, "keys.json"), "r") as f:
    keys = jsonpickle.decode(f.read())


def multireplace(string, replacements, ignore_case=False):
    """
    Given a string and a replacement map, it returns the replaced string.

    :param str string: string to execute replacements on
    :param dict replacements: replacement dictionary {value to find: value to replace}
    :param bool ignore_case: whether the match should be case insensitive
    :rtype: str

    """
    if not replacements:
        # Edge case that'd produce a funny regex and cause a KeyError
        return string

    # If case insensitive, we need to normalize the old string so that later a replacement
    # can be found. For instance with {"HEY": "lol"} we should match and find a replacement for "hey",
    # "HEY", "hEy", etc.
    if ignore_case:

        def normalize_old(s):
            return s.lower()

        re_mode = re.IGNORECASE

    else:

        def normalize_old(s):
            return s

        re_mode = 0

    replacements = {normalize_old(key): val for key, val in replacements.items()}

    # Place longer ones first to keep shorter substrings from matching where the longer ones should take place
    # For instance given the replacements {'ab': 'AB', 'abc': 'ABC'} against the string 'hey abc', it should produce
    # 'hey ABC' and not 'hey ABc'
    rep_sorted = sorted(replacements, key=len, reverse=True)
    rep_escaped = map(re.escape, rep_sorted)

    # Create a big OR regex that matches any of the substrings to replace
    pattern = re.compile("|".join(rep_escaped), re_mode)

    # For each match, look up the new string in the replacements, being the key the normalized old string
    return pattern.sub(
        lambda match: replacements[normalize_old(match.group(0))], string
    )


class CellRendererTextWindow(Gtk.Window):
    def __init__(self, l: list):
        super().__init__()
        self.liststore = Gtk.ListStore(str, str, str)
        for row in l:
            self.liststore.append([row[0], row[1], row[2]])
        treeview = Gtk.TreeView(model=self.liststore)

        renderer_text_1 = Gtk.CellRendererText()
        modifier = Gtk.TreeViewColumn("Modifier", renderer_text_1, text=0)
        treeview.append_column(modifier)

        renderer_text_2 = Gtk.CellRendererText()
        key = Gtk.TreeViewColumn("Key", renderer_text_2, text=1)
        treeview.append_column(key)

        renderer_text_3 = Gtk.CellRendererText()
        desc = Gtk.TreeViewColumn("Description", renderer_text_3, text=2)
        treeview.append_column(desc)
        sw = Gtk.ScrolledWindow()
        sw.add(treeview)
        self.add(sw)


def keyslist():
    keyslist = []
    arrow = "[red] => [/RED]"

    for key in keys:
        if hasattr(key, "submappings"):
            keyslist.extend(
                [
                    " + ".join(key.modifiers),
                    arrow.join([key.key, subkey.key]),
                    subkey.desc,
                ]
                for subkey in key.submappings
            )
        else:
            keyslist.append([" + ".join(key.modifiers), key.key, key.desc])

    replace_dict = {
        "control": "Ctrl",
        "shift": "Shift",
        "Up": "",
        "Down": "",
        "Left": "",
        "Right": "",
        "mod1": "Alt",
        "mod4": "",
        "Return": "Enter",
        "grave": "`",
        "minus": "-",
        "equal": "=",
        "Enter": "",
        "XF86AudioMute": "",
        "XF86AudioLowerVolume": "",
        "XF86AudioRaiseVolume": "",
        "XF86AudioPrev": "",
        "XF86AudioNext": "",
        "XF86AudioMicMute": "",
        "XF86AudioPlay": "",
        "XF86AudioPause": "",
        "XF86MonBrightnessUp": " +",
        "XF86MonBrightnessDown": " -"
        # "Escape": "Esc",
    }
    for row_index, row in enumerate(keyslist):
        for col_index, string in enumerate(row):
            if string in [
                "Update system",
                # "XF86MonBrightnessUp",
                # "XF86MonBrightnessDown",
            ]:
                continue
            else:
                keyslist[row_index][col_index] = multireplace(
                    string, replace_dict, False
                )

    return keyslist


def gtk(l: list):
    win = CellRendererTextWindow(l)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


def md(l: list):
    headers = ["Modifier", "Key", "Description"]
    d = [dict(zip(headers, list)) for list in l]
    return markdownTable(d).setParams(row_sep="markdown", quote=False).getMarkdown()


def main():
    k = keyslist()
    parser = argparse.ArgumentParser(
        description="Open keybindings in GTK+ window/Generate keybindings markdown table"
    )
    parser.add_argument("action", type=str, help="[gtk/md] action to be chosen")
    args = parser.parse_args()
    if args.action == "gtk":
        gtk(k)
    elif args.action == "md":
        # exit(0)
        print(md(k))
    else:
        parser.error("you need to provide an action")


if __name__ == "__main__":
    main()
