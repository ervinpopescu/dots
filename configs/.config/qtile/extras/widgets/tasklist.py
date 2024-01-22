# import os
# import subprocess

from libqtile import widget


class TaskList(widget.TaskList):
    defaults = [("popup", "", "function that handles thumbnails")]

    def __init__(self, **config):
        widget.TaskList.__init__(self, **config)
        self.add_defaults(TaskList.defaults)
        self.add_callbacks({"Button3": self.close_window})
        # self.win = None
        # self.mouse_pos: tuple[int, int] = None

    def _configure(self, qtile, bar):
        widget.TaskList._configure(self, qtile, bar)

    def close_window(self):
        if self.clicked:
            window = self.clicked
            window.kill()

    def draw_icon(self, surface, offset):
        if not surface:
            return

        x = offset + self.borderwidth + self.padding_x
        y = self.padding_y + self.borderwidth

        self.drawer.ctx.save()
        self.drawer.ctx.translate(x, y)
        self.drawer.ctx.set_source(surface)
        self.drawer.ctx.paint()
        self.drawer.ctx.restore()

    # def get_win(self, x, y):
    #     box_start = self.margin_x
    #     for box_end, win in zip(self._box_end_positions, self.windows):
    #         if box_start <= x <= box_end:
    #             return win
    #         else:
    #             box_start = box_end + self.spacing
    #     # not found any , return None
    #     return None

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

    # def mouse_enter(self, x, y):
    #     # if self.bar.screen.group.layout.name != "max":
    #     self.win = self.get_win(x, y)
    #     if self.win:
    #         xwd = f"xwd -id {self.win.wid}".split()
    #         convert = "convert xwd:- /tmp/thumbnail.png".split()
    #         p1 = subprocess.Popen(xwd, stdout=subprocess.PIPE)
    #         subprocess.call(convert, stdin=p1.stdout)
    #         if callable(self.popup):
    #             self.popup(self.win)
    #             try:
    #                 os.remove("/tmp/thumbnail.png")
    #             except OSError:
    #                 pass
    #     self.win = None
