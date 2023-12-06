#!/usr/bin/python

import signal
import subprocess
from time import sleep

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Gio, GLib, GObject
from gi.repository import Gtk as gtk


class Indicator:
    def __init__(self):
        self.vp = None
        self.vpc()
        icons_folder = "/usr/share/icons/Papirus-Dark/symbolic/status"
        self.filenames = {
            "ic": f"{icons_folder}/power-profile-balanced-symbolic.svg",
            "bs": f"{icons_folder}/power-profile-power-saver-symbolic.svg",
            "ep": f"{icons_folder}/power-profile-performance-symbolic.svg",
        }
        self.icon_filename: str = self.filenames[self.vp]
        self.indicator = appindicator.Indicator.new(
            "customtray",
            self.icon_filename,
            appindicator.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.menu())
        self.vpc()
        self.change_icon()
        self.start_timer()

    def vpc(self):
        vpcheck = (
            subprocess.check_output("ideapad-perf -vp".split()).decode("utf-8").strip()
        )
        match vpcheck:
            case "Running in Extreme Performance mode.":
                self.vp = "ep"
            case "Running in Intelligent Cooling mode.":
                self.vp = "ic"
            case "Running in Battery Saving mode.":
                self.vp = "bs"

    def menu(self):
        menu = gtk.Menu()

        title = gtk.MenuItem(label="Performance mode")
        title.set_sensitive(False)
        menu.append(title)

        mode_1 = gtk.RadioMenuItem(label="Extreme Performance")
        menu.append(mode_1)
        if self.vp == "ep":
            mode_1.set_active(True)
        mode_1.connect("activate", self.change_performance_mode, "ep")

        mode_2 = gtk.RadioMenuItem(label="Intelligent Cooling", group=mode_1)
        menu.append(mode_2)
        if self.vp == "ic":
            mode_2.set_active(True)
        mode_2.connect("activate", self.change_performance_mode, "ic")

        mode_3 = gtk.RadioMenuItem(label="Battery Saving", group=mode_1)
        menu.append(mode_3)
        if self.vp == "bs":
            mode_3.set_active(True)
        mode_3.connect("activate", self.change_performance_mode, "bs")

        menu.append(gtk.SeparatorMenuItem())

        quit = gtk.MenuItem(label="Quit")
        menu.append(quit)
        quit.connect("activate", self.quit, "quit")

        menu.show_all()
        return menu

    def change_performance_mode(self, source, string):
        subprocess.call(
            f"ideapad-perf -p {string}".split(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.vpc()
        if self.vp == string:
            self.indicator.set_icon_full(self.filenames[string], "")

    def change_icon(self):
        initial_vp = self.vp
        self.vpc()
        if initial_vp != self.vp:
            self.indicator.set_icon_full(self.filenames[self.vp], "")
            self.indicator.set_menu(self.menu())
        return True

    def start_timer(self):
        GLib.timeout_add(5000, self.change_icon)

    def quit(self):
        gtk.main_quit(*self)


if __name__ == "__main__":
    indicator = Indicator()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    gtk.main()
