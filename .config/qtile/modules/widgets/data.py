from libqtile.lazy import lazy

from extras import Data
from modules.settings import cmds, text_font


def data():
    return Data(
        font=text_font,
        fontsize=34,
        mouse_callbacks={"Button1": lazy.spawn(cmds["htop"])},
        padding=10,
        update_interval=3600,
    )
