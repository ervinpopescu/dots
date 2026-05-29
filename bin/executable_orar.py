#!/usr/bin/env python3

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path

# Optional dependencies handling
try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
except (ImportError, ValueError):
    Gtk = None

try:
    import gspread
except ImportError:
    gspread = None

# Constants
CACHE_DIR = Path.home() / ".local" / "state"
ORAR_JSON = CACHE_DIR / "orar.json"


def dunstify(string):
    cmd = ["dunstify", "-t", "5000", "-a", "orar", "-u", "normal", "-r", "311213", "Error!", string]
    try:
        subprocess.run(cmd, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print(f"Error: {string}", file=sys.stderr)


class CellRendererTextWindow(Gtk.Window):
    def __init__(self, l: list):
        super().__init__()
        self.liststore = Gtk.ListStore(str, str, str, str)
        for row in l:
            # Ensure row has enough elements
            row_padded = row + [""] * (4 - len(row))
            self.liststore.append(row_padded[:4])
            
        treeview = Gtk.TreeView(model=self.liststore)
        Gtk.TreeViewColumnSizing(2)
        treeview.set_grid_lines(3)

        cols = [
            ("ZI", 0, 100),
            ("INTERVAL ORAR", 1, 150),
            ("444Ca", 2, 200),
            ("444Cb", 3, 200)
        ]

        for title, idx, width in cols:
            renderer = Gtk.CellRendererText()
            renderer.set_alignment(0.5, 0.5)
            col = Gtk.TreeViewColumn(title, renderer, text=idx)
            col.set_fixed_width(width)
            col.set_alignment(0.5)
            treeview.append_column(col)

        sw = Gtk.ScrolledWindow()
        sw.add(treeview)
        self.add(sw)


def get_schedule(refresh: bool):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if refresh:
        if not gspread:
             dunstify("gspread module not found. Cannot refresh.")
             sys.exit(1)

        try:
            gc = gspread.oauth()
            # Note: This URL might be private/invalid. Consider moving to config if needed.
            sh = gc.open_by_url(
                "https://docs.google.com/spreadsheets/d/1n-rQuzX04B-40f-xlXRoTUjcCqWrpj2qKNtjCUHER7c"
            )
            worksheet = sh.worksheet("Orar")
            list_of_lists = worksheet.get("A1:F44")
            
            # Cleaning data logic preserved from original
            list_of_lists = [el for el in list_of_lists if len(el) >= 3]
            if list_of_lists:
                list_of_lists.pop(0) # Remove header
            
            cleaned_list = []
            for row in list_of_lists:
                 # Original logic: list.pop(0) -> remove first col?
                 # Assuming first col was empty or index? 
                 # Original: list.pop(0). 
                 if len(row) > 0:
                     row.pop(0)
                 
                 if len(row) == 3:
                     row.append(row[-1])
                 cleaned_list.append(row)

            with open(ORAR_JSON, "w") as f:
                json.dump(cleaned_list, f)
            return cleaned_list
        except Exception as e:
            dunstify(f"Refresh failed: {e}")
            sys.exit(1)
    else:
        if ORAR_JSON.exists():
            with open(ORAR_JSON, "r") as f:
                return json.load(f)
        else:
            dunstify(f"`{ORAR_JSON.name}` not found,\nplease run `orar.py -r`")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Script care afișează orarul de pe Google Sheets"
    )
    parser.add_argument(
        "-r",
        "--refresh",
        action="store_true",
        help="refresh the json file",
    )
    args = parser.parse_args()
    
    list_of_lists = get_schedule(args.refresh)
    
    if not args.refresh:
        if Gtk is None:
             print("Error: Gtk (python3-gi) not found. Cannot display GUI.", file=sys.stderr)
             sys.exit(1)
             
        win = CellRendererTextWindow(list_of_lists)
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        Gtk.main()


if __name__ == "__main__":
    main()
