#!/bin/python

# import datetime

import argparse
import json
import os
import subprocess

import gi
import gspread

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

def dunstify(string):
    command = "dunstify -t 5000 -a orar -u normal -r 311213".split()
    subprocess.run(command + ["Error!", string])

class CellRendererTextWindow(Gtk.Window):
    def __init__(self, l: list):
        super().__init__()
        self.liststore = Gtk.ListStore(str, str, str, str)
        for row in l:
            self.liststore.append([row[0], row[1], row[2], row[3]])
        treeview = Gtk.TreeView(model=self.liststore)
        Gtk.TreeViewColumnSizing(2)
        treeview.set_grid_lines(3)

        renderer_text_1 = Gtk.CellRendererText()
        renderer_text_1.set_alignment(0.5, 0.5)
        zi = Gtk.TreeViewColumn("ZI", renderer_text_1, text=0)
        zi.set_fixed_width(100)
        zi.set_alignment(0.5)
        treeview.append_column(zi)

        renderer_text_2 = Gtk.CellRendererText()
        renderer_text_2.set_alignment(0.5, 0.5)
        interval = Gtk.TreeViewColumn("INTERVAL ORAR", renderer_text_2, text=1)
        interval.set_fixed_width(150)
        interval.set_alignment(0.5)
        treeview.append_column(interval)

        renderer_text_3 = Gtk.CellRendererText()
        renderer_text_3.set_alignment(0.5, 0.5)
        semigr_a = Gtk.TreeViewColumn("444Ca", renderer_text_3, text=2)
        semigr_a.set_fixed_width(200)
        semigr_a.set_alignment(0.5)
        treeview.append_column(semigr_a)

        renderer_text_4 = Gtk.CellRendererText()
        renderer_text_4.set_alignment(0.5, 0.5)
        semigr_b = Gtk.TreeViewColumn("444Cb", renderer_text_4, text=3)
        semigr_b.set_fixed_width(200)
        semigr_b.set_alignment(0.5)
        treeview.append_column(semigr_b)

        sw = Gtk.ScrolledWindow()
        sw.add(treeview)
        self.add(sw)

def get_schedule(refresh: bool):
    if refresh:
        gc = gspread.oauth()
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1n-rQuzX04B-40f-xlXRoTUjcCqWrpj2qKNtjCUHER7c")
        worksheet = sh.worksheet("Orar")
        list_of_lists = worksheet.get("A1:F44")
        for list in list_of_lists:
            if len(list) < 3:
                list_of_lists.remove(list)
        res = [el for el in list_of_lists if el != []]
        list_of_lists = res
        list_of_lists.pop(0)
        for list in list_of_lists:
            list.pop(0)
            if len(list) == 3:
                list.append(list[-1])

        with open("/home/ervin/.local/state/orar.json", "w") as f:
            json.dump(list_of_lists, f)
        return list_of_lists
    else:
        if "orar.json" in os.listdir("/home/ervin/.local/state/"):
            with open("/home/ervin/.local/state/orar.json", "r") as f:
                local = json.load(f)
            list_of_lists = local
            list_of_dicts = []
            i = 0
            while i in range(len(list_of_lists)):
                current = list_of_lists[i]
                day = current[0]
                if day != "":
                    list_of_dicts.append(
                        {
                            "day": day,
                            "list": [current[1:]],
                        }
                    )
                    current_day = day
                else:
                    list_of_dicts[
                        next(
                            (
                                j
                                for j, item in enumerate(list_of_dicts)
                                if item["day"] == current_day
                            )
                        )
                    ]["list"].append(current[1:])
                i += 1

            for d in list_of_dicts:
                d["dict"] = {}
                for l in d["list"]:
                    l[0] = l[0].split("-")[0]
                    d["dict"][l[0]] = l[2]
                del d["list"]

            # print(json.dumps(list_of_dicts, indent=2))
            return list_of_lists

        else:
            dunstify("`orar.json` not found,\nplease run `orar.py -r`")
            exit(1)

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
        win = CellRendererTextWindow(list_of_lists)
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        Gtk.main()

if __name__ == "__main__":
    main()
