# from extras.widgets import TaskList
from qtile_extras.widget import TaskList

from modules.settings import colors, settings

# icon_size = settings["bar_height"] - 12
# margin_y = icon_size + 4
# margin_x = margin_y - icon_size
# padding_x = (margin_y - icon_size) // 2
# padding_y = 0
margin_y = -5
margin_x = 5
# padding_x = 0


def task_list():
    return TaskList(
        border=colors["darkblue"],
        highlight_method="border",
        # rounded=False,
        # icon_only=True,
        # theme_mode="preferred",
        # theme_path="/usr/share/icons/Papirus",
        # padding_x=padding_x,
        # padding_y=padding_y,
        # icon_size=icon_size,
        margin_x=margin_x,
        margin_y=margin_y,
        # txt_floating="",
        # txt_maximized="",
        # txt_minimized="",
        font=settings["text_font"],
        fontsize=settings["font_size"],
    )
