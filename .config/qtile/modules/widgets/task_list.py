from extras import TaskList
from modules.functions import no_text
from modules.settings import bar_height, colors

task_list = TaskList(
    border=colors["fg1"],
    highlight_method="block",
    icon_size=bar_height - 7,
    margin_x=4,
    # margin_y=65,
    margin_y=bar_height - 8,
    padding_x=0,
    padding_y=-1,
    parse_text=no_text,
    rounded=True,
    theme_mode="preferred",
    theme_path="/usr/share/icons/Papirus",
    txt_floating="",
    txt_maximized="",
    txt_minimized="",
    # popup=thumbnail,
    # max_title_width=1,
    # txt_floating="🗗 ",
    # txt_maximized="🗖 ",
    # txt_minimized="🗕 ",
)
