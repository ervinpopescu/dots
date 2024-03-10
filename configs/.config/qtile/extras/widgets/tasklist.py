import contextlib
import os
import subprocess

from libqtile.log_utils import logger
from libqtile.widget import base
from qtile_extras import widget


class TaskList(widget.TaskList):
    defaults = [
        # (
        #     "popup",
        #     None,
        #     "function that handles thumbnails",
        # ),
        (
            "icon_only",
            False,
            "Hide all text and just show icons (X11 only)",
        )
    ]

    def __init__(self, **config):
        widget.TaskList.__init__(self, **config)
        self.add_defaults(TaskList.defaults)
        self.add_callbacks({"Button3": self.close_window})

    #     # self.win = None
    #     # self.mouse_pos: tuple[int, int] = None

    def _configure(self, qtile, bar):
        base._Widget._configure(self, qtile, bar)

        if qtile.core.name == "wayland" and self.icon_size != 0:
            # Disable icons
            self.icon_size = 0
            logger.warning("TaskList icons not supported in Wayland.")
            if self.icon_only:
                self.icon_only = False
                logger.info("'icon_only' mode disabled.")

        if self.icon_only:
            if self.icon_size == 0:
                self.icon_size = None
            self.parse_text = lambda _: ""
        if self.icon_size is None:
            self.icon_size = self.bar.height - 2 * (self.borderwidth + self.margin_y)

        if self.fontsize is None:
            calc = self.bar.height - self.margin_y * 2 - self.borderwidth * 2 - self.padding_y * 2
            self.fontsize = max(calc, 1)
        self.layout = self.drawer.textlayout(
            "", "ffffff", self.font, self.fontsize, self.fontshadow, wrap=False
        )
        self.setup_hooks()

    def close_window(self):
        if self.clicked:
            window = self.clicked
            window.kill()

    # def draw_icon(self, surface, offset):
    #     if not surface:
    #         return

    #     x = offset + self.borderwidth + self.padding_x
    #     # y = self.padding_y + self.borderwidth
    #     y = (self.height - self.icon_size) // 2

    #     self.drawer.ctx.save()
    #     self.drawer.ctx.translate(x, y)
    #     self.drawer.ctx.set_source(surface)
    #     self.drawer.ctx.paint()
    #     self.drawer.ctx.restore()

    # TODO: Generating thumbnails is not yet🙂 implemented
    # since qtile hides windows (i.e. sets the windows to hidden)
    # when the window is not visible or its group is not visible

    # def get_win(self, x, y):
    #     box_start = self.margin_x
    #     for box_end, win in zip(self._box_end_positions, self.windows):
    #         if box_start <= x <= box_end:
    #             return win
    #         else:
    #             box_start = box_end + self.spacing
    #     # not found any , return None
    #     return None
    #
    # def get_mouse_pos(self):
    #     _mouse_pos = list(self.qtile.core.get_mouse_position())
    #     if (_mouse_pos[0] > self.offset and _mouse_pos[0] < self.offset + self.length) and (
    #         _mouse_pos[1] < self.height
    #     ):
    #         self.mouse_pos = _mouse_pos
    #         self.mouse_pos[0] = self.mouse_pos[0] - self.offset
    #     else:
    #         self.mouse_pos = None
    #     self.timeout_add(1, self.get_mouse_pos)
    #
    # def mouse_enter(self, x, y):
    #     if self.bar.screen.group.layout.name == "max":
    #         return
    #     self.win = self.get_win(x, y)
    #     logger.debug(self.win)
    #     if self.win:
    #         self.call_popup()
    #     self.win = None
    #
    # def call_popup(self):
    #     xwd = f"xwd -id {self.win.wid}".split()
    #     convert = "convert xwd:- PNG:-".split()
    #     p1 = subprocess.Popen(xwd, stdout=subprocess.PIPE)
    #     image = subprocess.check_output(convert, stdin=p1.stdout)
    #     logger.log(type(image))
    #     if callable(self.popup):
    #         self.popup(self.win)
