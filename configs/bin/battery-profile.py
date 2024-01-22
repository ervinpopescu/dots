#!/usr/bin/python

import signal
import subprocess

import gi

gi.require_version("AppIndicator3", "0.1")
gi.require_version("Gtk", "3.0")

from gi.repository import AppIndicator3 as appindicator
from gi.repository import GLib
from gi.repository import Gtk as gtk


class Indicator:
    def __init__(self):
        self.battery_profile = None
        self.vbc()
        icons_folder = "/usr/share/icons/Papirus-Dark/symbolic/status"
        self.filenames = {
            "rc": f"{icons_folder}/battery-good-charging-symbolic.svg",
            "bc": f"{icons_folder}/battery-good-symbolic.svg",
            "off": f"{icons_folder}/battery-missing-symbolic.svg",
        }
        self.icon_filename: str = self.filenames[self.battery_profile]
        self.indicator = appindicator.Indicator.new(
            "customtray",
            self.icon_filename,
            appindicator.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.menu())
        self.change_icon()
        self.start_timer()

    def vbc(self):
        f = subprocess.check_output("ideapad-perf -vb".split())
        match f.decode("utf-8").strip():
            case "Rapid Charge mode is on, Battery Conservation mode is off.":
                self.battery_profile = "rc"
            case "Rapid Charge mode is off, Battery Conservation mode is on.":
                self.battery_profile = "bc"
            case "Rapid Charge mode is off, Battery Conservation mode is off.":
                self.battery_profile = "off"

    def menu(self):
        menu = gtk.Menu()

        title = gtk.MenuItem(label="Battery mode")
        title.set_sensitive(False)
        menu.append(title)

        mode_1 = gtk.RadioMenuItem(label="Rapid charge")
        menu.append(mode_1)
        if self.battery_profile == "rc":
            mode_1.set_active(True)
        mode_1.connect("activate", self.change_mode, "rc")

        mode_2 = gtk.RadioMenuItem(label="Battery conservation", group=mode_1)
        if self.battery_profile == "bc":
            mode_2.set_active(True)
        menu.append(mode_2)
        mode_2.connect("activate", self.change_mode, "bc")

        mode_3 = gtk.RadioMenuItem(label="Off", group=mode_1)
        menu.append(mode_3)
        if self.battery_profile == "off":
            mode_3.set_active(True)
        mode_3.connect("activate", self.change_mode, "off")

        menu.append(gtk.SeparatorMenuItem())

        exit_tray = gtk.MenuItem(label="Quit")
        menu.append(exit_tray)
        exit_tray.connect("activate", self.quit, "quit")

        menu.show_all()
        return menu

    def change_mode(self, source, string):
        subprocess.call(
            f"ideapad-perf -b {string}".split(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.vbc()
        if self.battery_profile == string:
            self.indicator.set_icon_full(self.filenames[string], "")

    def change_icon(self):
        initial_bp = self.battery_profile
        self.vbc()
        if initial_bp != self.battery_profile:
            self.indicator.set_icon_full(self.filenames[self.battery_profile], "")
            self.indicator.set_menu(self.menu())
        return True

    def start_timer(self):
        GLib.timeout_add(5000, self.change_icon)

    def quit(self):
        gtk.main_quit(*self)


if __name__ == "__main__":
    Indicator()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    gtk.main()
