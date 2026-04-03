from __future__ import division, print_function, unicode_literals
import subprocess
import os
import xcffib
import shlex
import asyncio

import psutil  # type: ignore
from copy import deepcopy
from qtile_extras.popup.toolkit import PopupImage
from modules.path import config_path
from libqtile.utils import create_task
from libqtile.log_utils import logger
from libqtile.widget import base, systray
from qtile_extras import widget
from qtile_extras.widget.mixins import ExtendedPopupMixin

import itertools
import struct
import time
# import io
# import png

# :python3:buffer: we need to get a binary stream in both
# Python 2 and Python 3.
def binary(stream):
    if hasattr(stream, "buffer"):
        return stream.buffer
    else:
        return stream

class FormatError(Exception):
    pass

class NotImplemented(Exception):
    pass

class Channel:
    def __init__(self, **k):
        self.__dict__.update(k)

class XWD:
    def __init__(self, input, xwd_header=None):
        if xwd_header:
            self.__dict__.update(xwd_header)
        self.xwd_header = xwd_header
        self.info_dict = dict(
            h=self.pixmap_height, w=self.pixmap_width, xwd_header=xwd_header
        )
        self.input = input

    def info(self):
        return dict(self.info_dict)

    def uni_format(self):
        """
        Return the "universal format" for the XWD file.
        As a side effect, compute and cache various
        intermediate values (such as shifts and depths).
        """

        if "_uni_format" in self.__dict__:
            return self._uni_format

        # Check visual_class.
        # The following table from http://www.opensource.apple.com/source/tcl/tcl-87/tk/tk/xlib/X11/X.h is assumed:
        # StaticGray    0
        # GrayScale     1
        # StaticColor   2
        # PseudoColor   3
        # TrueColor     4
        # DirectColor   5

        if self.visual_class != 4:
            # TrueColor
            raise NotImplementedError(
                "Cannot handle visual_class {!r}".format(self.visual_class)
            )

        # Associate each mask with its channel colour.
        channels = [
            Channel(name="R", mask=self.red_mask),
            Channel(name="G", mask=self.green_mask),
            Channel(name="B", mask=self.blue_mask),
        ]

        # If fails: some masks are the same.
        assert len(set(c.mask for c in channels)) == 3

        # Sort Most Significant first
        channels = sorted(channels, key=lambda x: x.mask, reverse=True)

        # Check that each mask is contiguous.
        for channel in channels:
            assert is_contiguous(channel.mask)

        # Check that each mask abuts the next...
        for channel, successor in zip(channels, channels[1:]):
            assert is_contiguous(channel.mask + successor.mask)

        # ... check that the last mask is on the right.
        # If fails: least significant bit is unused.
        # :todo: if it ever occurs in wild, implement a padding
        # channel, eg: RGB5X1.
        assert channels[-1].mask & 1

        # Annotate each channel with its shift and bitdepth.
        for c in channels:
            c.shift = ffs(c.mask)
            c.bits = (c.mask >> c.shift).bit_length()

        self.channels = channels

        v = ""
        for (bits, chans) in itertools.groupby(channels, lambda c: c.bits):
            v += "".join(c.name for c in chans)
            v += str(bits)
        self._uni_format = v
        return self.uni_format()

    def __iter__(self):
        while True:
            bs = self.input.read(self.bytes_per_line)
            if len(bs) == 0:
                break
            yield list(itertools.chain(*self.pixels(bs)))

    def __len__(self):
        return self.pixmap_height

    def pixels(self, row):
        self.uni_format()

        # bytes per pixel
        bpp = self.bits_per_pixel // 8
        if bpp * 8 != self.bits_per_pixel or bpp > 4:
            raise NotImplementedError(
                "Cannot handle bits_per_pixel of {!r}".format(self.bits_per_pixel)
            )

        for s in range(0, len(row), bpp):
            pix = row[s: s + bpp]
            # pad to 4 bytes
            pad = b"\x00" * (4 - len(pix))
            if self.byte_order == 1:
                fmt = ">L"
                pix = pad + pix
            else:
                fmt = "<L"
                pix = pix + pad
            v, = struct.unpack(fmt, pix)

            cs = self.channels
            # Note: Could permute channels here
            # by permuting the `cs` list;
            # for example to convert BGR to RGB.
            pixel = tuple((v & c.mask) >> c.shift for c in cs)

            yield pixel

def xwd_open(f):
    # From XWDFile.h:
    # "Values in the file are most significant byte first."
    fmt = ">L"

    header = f.read(8)

    header_size, = struct.unpack(fmt, header[:4])

    # There are no magic numbers, so as a sanity check,
    # we check that the size is "reasonable" (< 65536)
    if header_size >= 65536:
        raise FormatError("header_size too big: {!r}".format(header[:4]))

    version, = struct.unpack(fmt, header[4:8])
    if version != 7:
        raise FormatError(
            "Sorry only version 7 supported, not version {!r}".format(version)
        )

    fields = [
        "pixmap_format",
        "pixmap_depth",
        "pixmap_width",
        "pixmap_height",
        "xoffset",
        "byte_order",
        "bitmap_unit",
        "bitmap_bit_order",
        "bitmap_pad",
        "bits_per_pixel",
        "bytes_per_line",
        "visual_class",
        "red_mask",
        "green_mask",
        "blue_mask",
        "bits_per_rgb",
        "colormap_entries",
        "ncolors",
        "window_width",
        "window_height",
        "window_x",
        "window_y",
        "window_bdrwidth",
    ]

    res = dict(header_size=header_size, version=version)
    for field in fields:
        v, = struct.unpack(fmt, f.read(4))
        res[field] = v

    xwd_header_size = 8 + 4 * len(fields)
    window_name_len = header_size - xwd_header_size

    if window_name_len <= 0:
        raise FormatError("Size in header, {!r}, is too small".format(xwd_header_size))

    window_name = f.read(window_name_len)[:-1]
    res["window_name"] = window_name

    # read, but ignore, the colours
    # color_fmt = fmt + ">H" * 3 + "B" + "B"
    for i in range(res["ncolors"]):
        f.read(12)

    xwd = XWD(input=f, xwd_header=res)
    return xwd

def ffs(x):
    """
    Returns the index, counting from 0, of the
    least significant set bit in `x`.
    """
    return (x & -x).bit_length() - 1

def is_contiguous(x):
    """
    Check that x is a contiguous series of binary bits.
    """
    return is_power_of_2((x >> ffs(x)) + 1)

def is_power_of_2(x):
    assert x > 0
    return not (x & (x - 1))

class TaskList(widget.TaskList, ExtendedPopupMixin):
    defaults = [
        (
            "icon_only",
            False,
            "Hide all text and just show icons (X11 only)",
        ),
    ]

    def __init__(self, **config):
        widget.TaskList.__init__(self, **config)
        self.add_defaults(TaskList.defaults)
        ExtendedPopupMixin.__init__(self, **config)
        self.add_defaults(ExtendedPopupMixin.defaults)
        self.add_callbacks({"Button2": self.close_window})
        self.prev_win = None
        self.win = None
        self.mouse_pos = None
        self.thumbnail_pid = None

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
    #
    def get_win(self, x, y):
        box_start = self.margin_x
        for box_end, win in zip(self._box_end_positions, self.windows):
            if box_start <= x <= box_end:
                return win
            else:
                box_start = box_end + self.spacing
        # not found any , return None
        return None

    def get_mouse_pos(self):
        _mouse_pos = list(self.qtile.core.get_mouse_position())
        if (_mouse_pos[0] > self.offset and _mouse_pos[0] < self.offset + self.length) and (
            _mouse_pos[1] < self.height
        ):
            self.mouse_pos = _mouse_pos
            self.mouse_pos[0] = self.mouse_pos[0] - self.offset
        else:
            self.mouse_pos = None
        self.timeout_add(1, self.get_mouse_pos)

    # def mouse_enter(self, x, y):
    #     create_task(self._mouse_enter(x, y))
    #     # task.add_done_callback(self._finished_task)  # This is optional

    async def _mouse_enter(self, x, y):
        # if self.bar.screen.group.layout.name == "max":
        #     return
        self.win = self.get_win(x, y)
        if self.win:
            original_map_state = self.win.window.get_attributes().map_state
            if original_map_state == xcffib.xproto.MapState.Unmapped:
                self.win.window.map()
            await self.start_feh(x, y)
            # await self._update_popup()
            self.extended_popup.show(**self.popup_show_args)
            logger.info("popup shown")
            if original_map_state == xcffib.xproto.MapState.Unmapped:
                self.win.hide()

    # def mouse_leave(self, x, y):
    #     if self.thumbnail_pid in psutil.pids():
    #         psutil.Process(self.thumbnail_pid).kill()
    #     self.win = None
    #     # self._kill_popup()

    async def _update_popup(self):
        rx1, tx1 = os.pipe()
        _ = await asyncio.create_subprocess_exec(
            *shlex.split(f"xwd -id {hex(self.win.wid)}"),
            stdout=tx1,
            # stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        os.close(tx1)

        # start = time.time()
        # stdout, _ = await xwd_proc.communicate()
        # logger.info(type(stdout))
        # stdout = io.BytesIO(stdout)
        # logger.info(type(stdout))
        # xwd = xwd_open(stdout)
        # # format = xwd.uni_format()
        # # assert format == "RGB8"
        # apng = png.from_array(xwd, "RGB;8")
        # stdout.close()
        # apng.save("xwd.png")
        # end = time.time()
        # logger.info(end - start)

        rx2, tx2 = os.pipe()
        await asyncio.create_subprocess_exec(
            *shlex.split("magick xwd:- -resize 400x300\\> PNG:-"),
            stdin=rx1,
            stdout=open(os.path.join(config_path, "xwd.png"), "wb"),
            stderr=subprocess.DEVNULL,
        )
        os.close(rx1)
        time.sleep(0.5)
        self._kill_popup()
        self.extended_popup = deepcopy(self.popup_layout)
        self.extended_popup._configure(self.qtile)
        self.extended_popup.update_controls(
            image=PopupImage(
                name="image",
                filename=os.path.join(config_path, "xwd.png"),
                pos_x=0,
                pos_y=0,
                width=1,
                height=1,
            ),
        )

    async def start_feh(self, x, y):
        rx1, tx1 = os.pipe()
        await asyncio.create_subprocess_exec(
            *shlex.split(f"xwd -id {hex(self.win.wid)}"),
            stdout=tx1,
            stderr=subprocess.DEVNULL,
        )
        os.close(tx1)
        rx2, tx2 = os.pipe()
        await asyncio.create_subprocess_exec(
            *shlex.split("magick xwd:- PNG:- "),
            stdin=rx1,
            stdout=tx2,
            stderr=subprocess.DEVNULL,
        )
        os.close(rx1)
        os.close(tx2)
        feh = await asyncio.create_subprocess_exec(
            *shlex.split("feh --scale-down --zoom fill --class feh_thumbnail -"),
            stdin=rx2,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        os.close(rx2)
        self.thumbnail_pid = feh.pid
        logger.info(self.thumbnail_pid)
        await asyncio.sleep(0.4)
        window = next(
            win
            for win in list(self.qtile.windows_map.values())
            if win.get_pid() == self.thumbnail_pid and not isinstance(win, systray.Icon)
        )
        if window:
            # add "SKIP_TASKBAR" to _NET_WM_STATE atom (for X11)
            if window.qtile.core.name == "x11":
                net_wm_state = list(
                    window.window.get_property("_NET_WM_STATE", "ATOM", unpack=int)
                )
                skip_taskbar = window.qtile.core.conn.atoms["_NET_WM_STATE_SKIP_TASKBAR"]
                if net_wm_state:
                    if skip_taskbar not in net_wm_state:
                        net_wm_state.append(skip_taskbar)
                else:
                    net_wm_state = [skip_taskbar]
                window.window.set_property("_NET_WM_STATE", net_wm_state)
                self.draw()
                box_start = self.margin_x
            x = x + self._box_end_positions[-1] - box_start
            # bar_y = self.bar.
            window.set_position_floating(x, self.bar.y - 300 - max(self.bar.margin) * 2)
