#!/bin/python

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GdkPixbuf, Gio, Gtk

(COLUMN_TEXT, COLUMN_PIXBUF) = range(2)

DRAG_ACTION = Gdk.DragAction.MOVE


class DragDropWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Volleyball Team")

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.add(hbox)

        vbox = Gtk.Box(spacing=12)
        hbox.pack_start(vbox, True, True, 0)

        self.iconview = DragSourceIconView()
        self.drop_area = DropArea()

        vbox.pack_start(self.iconview, True, True, 0)
        vbox.pack_start(self.drop_area, True, True, 0)

        self.drop_area.drag_dest_set_target_list(None)
        self.iconview.drag_source_set_target_list(None)

        self.drop_area.drag_dest_add_text_targets()
        self.iconview.drag_source_add_text_targets()


class DragSourceIconView(Gtk.IconView):
    def __init__(self):
        Gtk.IconView.__init__(self)
        self.set_text_column(COLUMN_TEXT)
        self.set_pixbuf_column(COLUMN_PIXBUF)

        model = Gtk.ListStore(str, GdkPixbuf.Pixbuf)
        self.set_model(model)
        self.add_item("Ervin Popescu", "im-user")
        self.add_item("Eddie Ionescu", "im-user")
        self.add_item("Adrian Emanuel", "im-user")

        self.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, [], DRAG_ACTION)
        self.connect("drag-data-get", self.on_drag_data_get)

    def on_drag_data_get(self, widget, drag_context, data, info, time):
        selected_path = self.get_selected_items()[0]
        selected_iter = self.get_model().get_iter(selected_path)
        text = self.get_model().get_value(selected_iter, COLUMN_TEXT)
        data.set_text(text, -1)

    def add_item(self, text, icon_name):
        pixbuf = Gtk.IconTheme.get_default().load_icon(icon_name, 16, 0)
        self.get_model().append([text, pixbuf])


class DropArea(Gtk.Grid):
    def __init__(self):
        Gtk.Grid.__init__(self)
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], DRAG_ACTION)
        self.connect("drag-data-received", self.on_drag_data_received)

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        text = data.get_text()
        print(f"Received text: {text}")

        label = Gtk.Label(label=text)
        self.attach(label, 1, 1, 1, 1)


win = DragDropWindow()
css_provider = Gtk.CssProvider()
file = Gio.File.new_for_path("/usr/share/themes/Adwaita/gtk-3.0/gtk.css")
css_provider.load_from_file(file)
screen = Gdk.Screen.get_default()
style_context = win.get_style_context()
style_context.add_provider_for_screen(
    screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)
# win.set_style_cont
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
