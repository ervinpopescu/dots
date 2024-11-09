from extras.widgets import TaskList
from modules.settings import colors, settings

margin_y = -1
margin_x = 5


def parse_text(title):
    for string in [
        " - Firefox",
        " - Chromium",
        " - Google Chrome",
        " — Firefox Developer Edition",
    ]:
        title = title.replace(string, "")
    return title


def task_list():
    return TaskList(
        border=colors["bg2"],
        highlight_method="block",
        margin_x=margin_x,
        margin_y=margin_y,
        font=settings["text_font"],
        fontsize=settings["font_size"] - 3,
        stretch=True,
        parse_text=parse_text,
        txt_floating="🗗 ",
        txt_maximized="🗖 ",
        txt_minimized="🗕 ",
    )
