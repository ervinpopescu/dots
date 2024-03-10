"""Proof-of-concept for a Tabbed layout in Qtile.

See GitHub page for more information: https://github.com/hanschen/qtile_tabbed

Created by Hans Chen (contact@hanschen.org).
"""

from libqtile import hook
from libqtile.layout.base import Layout, _ClientList, _SimpleLayoutBase


def count_windows(group, include_floating=True):
    count = 0
    for window in group.windows:
        if include_floating or not window.floating:
            count += 1
    return count


class Tab:
    """A tab representing a window."""

    def __init__(self, window):
        self.window = window
        self._left = 0
        self._right = 0

    def button_press(self, x, y):
        del y
        if self._left <= x < self._right:
            return self

    def draw(self, layout, left):
        if not layout.group.screen:
            return

        layout._layout.font_size = layout.fontsize
        layout._layout.text = self.window.name

        if self.window is layout.clients.current_client:
            fg = layout.active_fg
            bg = layout.active_bg
        elif self.window.urgent:
            fg = layout.urgent_fg
            bg = layout.urgent_bg
        else:
            fg = layout.inactive_fg
            bg = layout.inactive_bg

        ntabs = len(layout.clients)
        width = layout.group.screen.width / ntabs
        layout._layout.width = width
        layout._layout.colour = fg

        # get a text frame from the above
        framed = layout._layout.framed(
            border_width=0,
            border_color=bg,
            pad_x=0,
            pad_y=layout.padding_y,
        )

        # draw the text frame at the given point
        framed.draw_fill(left, 0, rounded=layout.rounded_tabs)

        self._left = left
        self._right = left + framed.width

        left += framed.width + layout.hspace
        return left


class ClientList(_ClientList):
    """Similar to libqtile.layout.base._ClientList, but allows wraping when
    shuffling windows.
    """

    def shuffle_up(self, maintain_index=True):
        """
        Shuffle the list. The current client swaps position with its
        predecessor. If maintain_index is True the current_index is adjusted,
        such that the same client stays current and goes up in list.
        """
        idx = self._current_idx
        if idx > 0:
            self.clients[idx], self.clients[idx - 1] = self[idx - 1], self[idx]
            if maintain_index:
                self.current_index -= 1
        else:
            self.clients.append(self.clients.pop(0))
            if maintain_index:
                self.current_index = len(self.clients) - 1

    def shuffle_down(self, maintain_index=True):
        """
        Shuffle the list. The current client swaps position with its successor.
        If maintain_index is True the current_index is adjusted,
        such that the same client stays current and goes down in list.
        """
        idx = self._current_idx
        if idx + 1 < len(self.clients):
            self.clients[idx], self.clients[idx + 1] = self[idx + 1], self[idx]
            if maintain_index:
                self.current_index += 1
        else:
            self.clients.insert(0, self.clients.pop(-1))
            if maintain_index:
                self.current_index = 0


class Tabbed(_SimpleLayoutBase):
    """Tabbed layout

    A simple layout that displays one window at a time, similar to the Max
    layout. The major difference from Max is that Tabbed will show a tab bar
    with all windows if there are more than one or two windows in the layout,
    depending on your settings.
    """

    defaults = [
        ("bg_color", "000000", "Background color of tab bar"),
        ("active_fg", "ffffff", "Foreground color of active tab"),
        ("active_bg", "000080", "Background color of active tab"),
        ("urgent_fg", "ffffff", "Foreground color of urgent tab"),
        ("urgent_bg", "ff0000", "Background color of urgent tab"),
        ("inactive_fg", "ffffff", "Foreground color of inactive tab"),
        ("inactive_bg", "606060", "Background color of inactive tab"),
        ("rounded_tabs", False, "Draw tabs rounded"),
        ("padding_y", 2, "Top and bottom padding for tab label"),
        ("hspace", 2, "Space between tabs"),
        ("font", "sans", "Font"),
        ("fontsize", 14, "Font pixel size"),
        ("fontshadow", None, "Font shadow color, default is None (no shadow)"),
        ("bar_height", 24, "Height of tab bar"),
        ("place_bottom", False, "Place tab bar at the bottom instead of top"),
        ("show_single_tab", True, "Show tabs if there is only a single tab"),
    ]

    def __init__(self, **config):
        _SimpleLayoutBase.__init__(self, **config)
        self.clients = ClientList()
        self.add_defaults(Tabbed.defaults)
        self._drawer = None
        self._panel = None
        self._tabs = {}

    def add(self, client):
        tab = Tab(client)
        self._tabs[client] = tab
        return super().add(client, 1)

    def clone(self, group):
        c = Layout.clone(self, group)
        c.clients = ClientList()
        return c

    def configure(self, client, screen_rect):
        if self.clients and client is self.clients.current_client:
            client.place(
                screen_rect.x,
                screen_rect.y,
                screen_rect.width,
                screen_rect.height,
                0,
                None,
            )
            client.unhide()
        else:
            client.hide()

    cmd_previous = _SimpleLayoutBase.previous
    cmd_next = _SimpleLayoutBase.next

    cmd_up = cmd_previous
    cmd_down = cmd_next

    cmd_left = cmd_previous
    cmd_right = cmd_next

    def cmd_shuffle_down(self):
        self.clients.shuffle_down()
        self.draw_panel()

    def cmd_shuffle_up(self):
        self.clients.shuffle_up()
        self.draw_panel()

    cmd_shuffle_left = cmd_shuffle_up
    cmd_shuffle_right = cmd_shuffle_down

    def draw_panel(self, *args):
        del args

        if not self._panel:
            return

        self._drawer.clear(self.bg_color)

        left = 0
        for client in self.clients:
            left = self._tabs[client].draw(self, left)

        self._drawer.draw(height=self.bar_height)

    def finalize(self):
        if self._panel:
            self._panel.kill()
        Layout.finalize(self)
        if self._drawer is not None:
            self._drawer.finalize()

    def hide(self):
        if self._panel:
            self._panel.hide()

    def layout(self, windows, screen_rect):
        if not self._show_tabs():
            body = screen_rect
            if self._panel:
                self._panel.hide()
        else:
            if self.place_bottom:
                body, panel = screen_rect.vsplit(screen_rect.height - self.bar_height)
            else:
                panel, body = screen_rect.vsplit(self.bar_height)
            self._resize_panel(panel)
            if self._panel:
                self._panel.unhide()
        Layout.layout(self, windows, body)

    def process_button_click(self, x, y, button):
        if button == 4:
            self.cmd_up()
        elif button == 5:
            self.cmd_down()
        else:
            for client in self.clients:
                tab = self._tabs[client].button_press(x, y)
                if tab:
                    self.group.focus(tab.window, False)

    def remove(self, win):
        super().remove(win)
        self._tabs.pop(win)
        self.draw_panel()

    def show(self, screen_rect):
        if not self._panel:
            self._create_panel(screen_rect)

        if not self._show_tabs():
            return

        if self.place_bottom:
            _, panel = screen_rect.vsplit(screen_rect.height - self.bar_height)
        else:
            panel, _ = screen_rect.vsplit(self.bar_height)
        self._resize_panel(panel)
        self._panel.unhide()

    def _create_drawer(self, screen_rect):
        if self._drawer is None:
            self._drawer = self._panel.create_drawer(
                screen_rect.width,
                self.bar_height,
            )
        else:
            self._drawer.width = screen_rect.width
        self._drawer.clear(self.bg_color)
        self._layout = self._drawer.textlayout(
            "", "#ffffff", self.font, self.fontsize, self.fontshadow, wrap=False
        )

    def _create_panel(self, screen_rect):
        self._panel = self.group.qtile.core.create_internal(
            screen_rect.x,
            screen_rect.y,
            screen_rect.width,
            self.bar_height,
        )
        self._create_drawer(screen_rect)
        self._panel.process_window_expose = self.draw_panel
        self._panel.process_button_click = self.process_button_click
        hook.subscribe.client_name_updated(self.draw_panel)
        hook.subscribe.focus_change(self.draw_panel)

    def _resize_panel(self, screen_rect):
        if self._panel:
            self._panel.place(
                screen_rect.x,
                screen_rect.y,
                screen_rect.width,
                screen_rect.height,
                0,
                None,
            )
            self._create_drawer(screen_rect)
            self.draw_panel()

    def _show_tabs(self):
        nwindows = count_windows(self.group, include_floating=False)
        if self.show_single_tab:
            return nwindows > 0
        else:
            return nwindows > 1
