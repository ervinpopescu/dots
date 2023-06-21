import json

from libqtile.bar import Bar
from libqtile.lazy import lazy

from modules.settings import group_layouts as def_group_layouts
from modules.settings import margin_size

ms = margin_size


@lazy.function
def window_to_prev_group(qtile):
    i = qtile.groups.index(qtile.current_group)
    if qtile.current_window is not None and i != 0:
        qtile.current_window.togroup(qtile.groups[i - 1].name)
        qtile.current_screen.toggle_group(qtile.groups[i - 1])


@lazy.function
def window_to_next_group(qtile):
    i = qtile.groups.index(qtile.current_group)
    if qtile.current_window is not None and i != 6:
        qtile.current_window.togroup(qtile.groups[i + 1].name)
        qtile.current_screen.toggle_group(qtile.groups[i + 1])


@lazy.function
def switch_win_in_group(qtile):
    qtile.current_group.focus_back()


@lazy.function
def toggle_minimize_all(qtile, current_group: bool = False):
    if not current_group:
        for group in qtile.groups:
            for win in group.windows:
                win.minimized = not win.minimized
                if win.minimized is False:
                    group.layout_all()
    else:
        for win in qtile.current_group.windows:
            win.minimized = not win.minimized
            if win.minimized is False:
                group.layout_all()


@lazy.function
def groupbox_disable_drag(qtile):
    widget = qtile.widgets_map["groupbox"]
    if widget.disable_drag is True:
        widget.disable_drag = False
    else:
        widget.disable_drag = True


def location():
    try:
        # location = requests.get("http://ip-api.com/json").json()
        with open("/home/ervin/.local/share/location.json", "r") as f:
            from_file = json.load(f)
        # from_ip = location["city"] + "," + location["countryCode"]
        # if from_ip == from_file["location"]:
        #     return from_ip
        # else:
        return from_file["location"]
    except Exception:
        return "Bucharest,RO"


def no_text(text):
    return ""


@lazy.function
def set_layout_all(qtile):
    """toggle layout for all groups between max and default"""
    groups = qtile.groups
    groups.pop()

    count = 0

    for g in groups:
        if g.eval("self.layout.name")[1] == "max":
            count = count + 1

    if count is not len(groups):
        for g in groups:
            g.setlayout("max")
    else:
        for g, l in zip(groups, def_group_layouts):
            g.setlayout(l)


@lazy.function
def set_layout_current(qtile):
    """toggle layout for current group between max and default"""
    groups = list(qtile.groups_map.keys())
    groups.pop()
    current_layout = qtile.current_screen.group.eval("self.layout.name")[1]
    current_group = qtile.current_screen.group.info()["name"]
    current_group_index = groups.index(current_group)
    if current_layout == "max":
        qtile.current_screen.group.setlayout(def_group_layouts[current_group_index])
    else:
        qtile.current_screen.group.setlayout("max")


@lazy.function
def toggle_gaps(qtile):
    bars = [x for x in qtile.current_screen.gaps if isinstance(x, Bar)]
    groups = qtile.groups
    for group in groups:
        # logger.info("%s", group.layout.single_margin)
        current_layout = group.layout
        if current_layout.margin != 0:
            current_layout.margin = 0
            if hasattr(current_layout, "single_margin"):
                current_layout.single_margin = 0
            for bar in bars:
                if isinstance(bar.margin, list):
                    bar.margin = [0] * 4
                else:
                    bar.margin = 0
                bar.draw()
        else:
            current_layout.margin = ms
            if hasattr(current_layout, "single_margin"):
                current_layout.single_margin = ms
            for bar in bars:
                if isinstance(bar.margin, list):
                    bar.margin = [ms] * 4
                else:
                    bar.margin = ms
                bar.draw()
        group.layout_all()


@lazy.function
def increase_gaps(qtile):
    groups = qtile.groups
    for group in groups:
        current_layout = group.layout
        if current_layout.margin > 0:
            current_layout.margin += 5
            if hasattr(current_layout, "single_margin"):
                current_layout.single_margin += 5
        group.layout_all()


@lazy.function
def decrease_gaps(qtile):
    groups = qtile.groups
    for group in groups:
        current_layout = group.layout
        if current_layout.margin > 6:
            current_layout.margin -= 5
            if hasattr(current_layout, "single_margin"):
                current_layout.single_margin -= 5
        group.layout_all()
