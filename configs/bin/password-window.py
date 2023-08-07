#!/bin/python

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class EntryWindow(Gtk.Window):
    def __init__(self):
        self.password: str = None
        super().__init__(name="password")
        self.set_wmclass("dialog", "dialog")
        self.set_default_size(560, 80)

        self.timeout_id = None

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.title = Gtk.Label()
        self.title.set_markup(
            "<big>Please enter your password for the system performance mode applet</big>"
        )
        self.title.set_line_wrap(True)
        # self.title.set_max_width_chars(90)
        vbox.pack_start(self.title, True, True, 0)

        self.entry = Gtk.Entry()
        self.entry.set_visibility(False)
        self.entry.set_max_length(30)
        self.entry.connect("activate", self.on_button_click)
        vbox.pack_start(self.entry, True, True, 0)

        hbox = Gtk.Box(spacing=6)
        vbox.pack_start(hbox, True, True, 0)

        self.check_visible = Gtk.CheckButton(label="Visible")
        self.check_visible.connect("toggled", self.on_visible_toggled)
        self.check_visible.set_active(False)
        hbox.pack_start(self.check_visible, True, True, 0)

        self.button = Gtk.Button(label="Submit")
        self.button.connect("clicked", self.on_button_click)
        hbox.pack_start(self.button, True, True, 0)

    def on_visible_toggled(self, button):
        value = button.get_active()
        self.entry.set_visibility(value)

    def on_button_click(self, widget):
        self.password = self.entry.get_text()
        Gtk.main_quit()


win = EntryWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()

print(win.password)
