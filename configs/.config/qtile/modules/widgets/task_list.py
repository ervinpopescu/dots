from extras.widgets import TaskList
from modules.settings import colors, settings

icon_size = settings["bar_height"] - 12
margin_y = icon_size + 4
margin_x = margin_y - icon_size
padding_x = (margin_y - icon_size) // 2
padding_y = 0
# margin_y = 0
# margin_x = 5
# padding_x = 0


def task_list():
    return TaskList(
        border=colors["darkblue"],
        highlight_method="block",
        icon_only=True,
        rounded=False,
        # rounded=True,
        theme_mode="preferred",
        theme_path="/usr/share/icons/Papirus",
        padding_x=padding_x,
        padding_y=padding_y,
        icon_size=icon_size,
        margin_x=margin_x,
        margin_y=margin_y,
        # popup=thumbnail,
        # max_title_width=1,
        # txt_floating="🗗 ",
        # txt_maximized="🗖 ",
        # txt_minimized="🗕 ",
        txt_floating="",
        txt_maximized="",
        txt_minimized="",
        font=settings["icon_font"],
    )
