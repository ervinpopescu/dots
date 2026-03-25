#!/usr/bin/python

import os
import signal
import subprocess

import gi

# from time import sleep

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Gio, GLib, GObject
from gi.repository import Gtk as gtk


class Indicator:
    def __init__(self):
        self.vp = None
        self.vpc()
        self.battery_profile = None
        self.vbc()

        icons_folder = "/usr/share/icons/Papirus-Dark/symbolic/status"
        # self.filenames = {
        #     "ic": f"{icons_folder}/power-profile-balanced-symbolic.svg",
        #     "bs": f"{icons_folder}/power-profile-power-saver-symbolic.svg",
        #     "ep": f"{icons_folder}/power-profile-performance-symbolic.svg",
        # }
        # self.icon_filename: str = self.filenames[self.vp]
        self.icon_filename = os.path.join(
            os.getenv(
                "XDG_DATA_HOME", os.path.join(os.path.expanduser("~/.local/share"))
            ),
            "systray_profile",
            "cogs.svg",
        )
        self.indicator = appindicator.Indicator.new(
            "customtray",
            self.icon_filename,
            appindicator.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.menu())
        self.vpc()
        # self.change_icon()
        # self.start_timer()

    def vbc(self):
        f = subprocess.check_output("ideapad-perf -vb".split())
        match f.decode("utf-8").strip():
            case "Rapid Charge mode is on, Battery Conservation mode is off.":
                self.battery_profile = "rc"
            case "Rapid Charge mode is off, Battery Conservation mode is on.":
                self.battery_profile = "bc"
            case "Rapid Charge mode is off, Battery Conservation mode is off.":
                self.battery_profile = "off"

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

        perf_mode_1 = gtk.RadioMenuItem(label="Extreme Performance")
        menu.append(perf_mode_1)
        if self.vp == "ep":
            perf_mode_1.set_active(True)
        perf_mode_1.connect("activate", self.change_performance_mode, "ep")

        perf_mode_2 = gtk.RadioMenuItem(label="Intelligent Cooling", group=perf_mode_1)
        menu.append(perf_mode_2)
        if self.vp == "ic":
            perf_mode_2.set_active(True)
        perf_mode_2.connect("activate", self.change_performance_mode, "ic")

        perf_mode_3 = gtk.RadioMenuItem(label="Battery Saving", group=perf_mode_1)
        menu.append(perf_mode_3)
        if self.vp == "bs":
            perf_mode_3.set_active(True)
        perf_mode_3.connect("activate", self.change_performance_mode, "bs")

        menu.append(gtk.SeparatorMenuItem())

        title = gtk.MenuItem(label="Battery mode")
        title.set_sensitive(False)
        menu.append(title)

        bat_mode_1 = gtk.RadioMenuItem(label="Rapid charge")
        menu.append(bat_mode_1)
        if self.battery_profile == "rc":
            bat_mode_1.set_active(True)
        bat_mode_1.connect("activate", self.change_battery_mode, "rc")

        bat_mode_2 = gtk.RadioMenuItem(label="Battery conservation", group=bat_mode_1)
        if self.battery_profile == "bc":
            bat_mode_2.set_active(True)
        menu.append(bat_mode_2)
        bat_mode_2.connect("activate", self.change_battery_mode, "bc")

        bat_mode_3 = gtk.RadioMenuItem(label="Off", group=bat_mode_1)
        menu.append(bat_mode_3)
        if self.battery_profile == "off":
            bat_mode_3.set_active(True)
        bat_mode_3.connect("activate", self.change_battery_mode, "off")

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
        # if self.vp == string:
        #     self.indicator.set_icon_full(self.filenames[string], "")

    def change_battery_mode(self, source, string):
        subprocess.call(
            f"ideapad-perf -b {string}".split(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.vbc()
        # if self.battery_profile == string:
        #     self.indicator.set_icon_full(self.filenames[string], "")

    def change_icon(self):
        initial_vp = self.vp
        self.vpc()
        if initial_vp != self.vp:
            # self.indicator.set_icon_full(self.filenames[self.vp], "")
            self.indicator.set_menu(self.menu())
        # for timer
        return True

    def start_timer(self):
        GLib.timeout_add(5000, self.change_icon)

    def quit(self):
        gtk.main_quit(*self)


if __name__ == "__main__":
    indicator = Indicator()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    gtk.main()
