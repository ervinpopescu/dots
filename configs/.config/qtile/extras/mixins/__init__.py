import os
from typing import TYPE_CHECKING

from libqtile.images import Img
from libqtile.log_utils import logger
from libqtile.popup import Popup

if TYPE_CHECKING:
    from typing import Any


class _BaseMixin:
    pass


class ThumbnailMixin(_BaseMixin):
    defaults = [
        ("thumbnail_delay", 1, "Time in seconds before thumbnail displayed"),
        ("thumbnail_background", "#000000", "Background colour for thumbnail text"),
        ("thumbnail_color", "#ffffff", "Font colur for thumbnail text"),
        ("thumbnail_font", "sans", "Font colour for thumbnail text"),
        ("thumbnail_fontsize", 12, "Font size for thumbnail text"),
        (
            "thumbnail_padding",
            4,
            "int for all sides or list for [top/bottom, left/right]",
        ),
    ]

    def __init__(self):
        self._thumbnail = None
        self._thumbnail_timer = None
        self.thumbnail_text = ""
        self.filename = "/tmp/thumbnail.png"
        self._thumbnail_padding = None

    def load_image(self):
        self.filename = os.path.expanduser(self.filename)

        if not os.path.exists(self.filename):
            logger.warning(f"Image does not exist: {self.filename}")
            return

        img = Img.from_path(self.filename)
        self.img = img

        if (img.width / img.height) >= (self.width / self.height):
            self.img.scale(width_factor=(self.width / img.width), lock_aspect_ratio=True)
        else:
            self.img.scale(height_factor=(self.height / img.height), lock_aspect_ratio=True)

    def get_mouse_pos(self, x, y):
        box_start = self.margin_x
        for box_end, win in zip(self._box_end_positions, self.windows):
            if box_start <= x <= box_end:
                return win
            else:
                box_start = box_end + self.spacing
        return None

    def _show_thumbnail(self, x, y):
        if self._thumbnail_padding is None:
            if isinstance(self.thumbnail_padding, int):
                self._thumbnail_padding = [self.thumbnail_padding] * 2

            elif not isinstance(self.thumbnail_padding, list) or len(self.thumbnail_padding) < 2:
                logger.warning("Invalid thumbnail padding. Defaulting to [4, 4]")
                self._thumbnail_padding = [4, 4]

        self._thumbnail = Popup(
            self.qtile,
            font=self.thumbnail_font,
            font_size=self.thumbnail_fontsize,
            foreground=self.thumbnail_color,
            background=self.thumbnail_background,
            vertical_padding=self._thumbnail_padding[0],
            horizontal_padding=self._thumbnail_padding[1],
            wrap=True,
        )

        # Size the popup
        self.img = None
        self.load_image()
        logger.warning("%s", self.img)
        self._thumbnail.text = self.thumbnail_text

        height = self._thumbnail.layout.height + (2 * self._thumbnail.vertical_padding)
        self._thumbnail.height = height
        width = self._thumbnail.layout.width + (2 * self._thumbnail.horizontal_padding)
        self._thumbnail.width = width

        # Position the thumbnail depending on bar position and orientation
        screen = self.bar.screen

        if screen.top == self.bar:
            x = min(self.offsetx, self.bar.width - width)
            y = self.bar.height

        elif screen.bottom == self.bar:
            x = min(self.offsetx, self.bar.width - width)
            y = screen.height - self.bar.height - height

        elif screen.left == self.bar:
            x = self.bar.width
            y = min(self.offsety, screen.height - height)

        else:
            x = screen.width - self.bar.width - width
            y = min(self.offsety, screen.height - height)

        self._thumbnail.x = x
        self._thumbnail.y = y

        self._thumbnail.clear()
        self._thumbnail.place()
        self._thumbnail.draw_image(self.img, 0, 0)
        self._thumbnail.draw_text()
        self._thumbnail.unhide()
        self._thumbnail.draw()

    def mouse_enter(self, x, y):
        if not self.configured or not self.thumbnail_text:
            return

        if not self._thumbnail_timer and not self._thumbnail:
            self._thumbnail_timer = self.timeout_add(
                self.thumbnail_delay, self._show_thumbnail, (x, y)
            )

    def mouse_leave(self, x, y):
        if self._thumbnail_timer and not self._thumbnail:
            self._thumbnail_timer.cancel()
            self._thumbnail_timer = None
            return
        else:
            self._thumbnail.hide()
            self._thumbnail.kill()
            self._thumbnail = None
            self._thumbnail_timer = None
