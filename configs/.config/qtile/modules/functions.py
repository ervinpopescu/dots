import contextlib
import json
import subprocess

import notify2
import psutil
from libqtile.bar import Bar
from libqtile.core.manager import Qtile
from libqtile.layout.floating import Floating
from libqtile.lazy import lazy
from libqtile.backend.base import Window

from modules.settings import settings

# from libqtile.log_utils import logger


ms = settings["margin_size"]
def_group_layouts = settings["group_layouts"]


@lazy.function
def window_to_prev_group(qtile: Qtile):
    i = qtile.groups.index(qtile.current_group)
    if qtile.current_window is not None and i != 0:
        qtile.current_window.togroup(qtile.groups[i - 1].name)
        qtile.current_screen.toggle_group(qtile.groups[i - 1])


@lazy.function
def window_to_next_group(qtile: Qtile):
    i = qtile.groups.index(qtile.current_group)
    if qtile.current_window is not None and i != 6:
        qtile.current_window.togroup(qtile.groups[i + 1].name)
        qtile.current_screen.toggle_group(qtile.groups[i + 1])


@lazy.function
def switch_win_in_group(qtile: Qtile):
    qtile.current_group.focus_back()


@lazy.function
def toggle_minimize_all(qtile: Qtile, current_group: bool = False):
    if not current_group:
        for group in qtile.groups:
            for win in group.windows:
                win.minimized = not win.minimized
                if not win.minimized:
                    group.layout_all()
    else:
        for win in qtile.current_group.windows:
            win.minimized = not win.minimized
            if not win.minimized:
                group.layout_all()


@lazy.function
def groupbox_disable_drag(qtile: Qtile):
    widget = qtile.widgets_map["groupbox"]
    widget.disable_drag = widget.disable_drag is not True


@lazy.function
def set_layout_all(qtile: Qtile):
    """toggle layout for all groups between max and default"""
    groups = qtile.groups
    groups.pop()

    count = 0

    for g in groups:
        if g.eval("self.layout.name")[1] == "max":
            count = count + 1

    if count != len(groups):
        for g in groups:
            g.setlayout("max")
    else:
        for g, l in zip(groups, def_group_layouts):
            g.setlayout(l)


@lazy.function
def set_layout_current(qtile: Qtile):
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
def toggle_gaps(qtile: Qtile):
    bars = [x for x in qtile.current_screen.gaps if isinstance(x, Bar)]
    groups = qtile.groups
    for group in groups:
        # logger.info("%s", group.layout.single_margin)
        current_layout = group.layout
        if current_layout.margin != 0:
            current_layout.margin = 0
            if hasattr(current_layout, "single_margin"):
                current_layout.single_margin = 0
            # for bar in bars:
            #     bar.margin = [0] * 4 if isinstance(bar.margin, list) else 0
            #     bar.draw()
        else:
            current_layout.margin = ms
            if hasattr(current_layout, "single_margin"):
                current_layout.single_margin = ms
            # for bar in bars:
            #     bar.margin = [ms] * 4 if not isinstance(bar.margin, list) else ms
            #     bar._configure(qtile, qtile.current_screen, reconfigure=True)
            #     bar.draw()
        group.layout_all()


@lazy.function
def increase_gaps(qtile: Qtile):
    groups = qtile.groups
    for group in groups:
        current_layout = group.layout
        if not isinstance(current_layout, Floating):
            if current_layout.margin > 0:
                current_layout.margin += 5
                if hasattr(current_layout, "single_margin"):
                    current_layout.single_margin += 5
            group.layout_all()
    # bar = qtile.current_screen.top
    # margin = bar.margin
    # margin = [margin + 5] * 4 if not isinstance(margin, list) else [m + 5 for m in margin]
    # bar._configure(qtile, qtile.current_screen, reconfigure=True)
    # bar.draw()


@lazy.function
def decrease_gaps(qtile: Qtile):
    groups = qtile.groups
    for group in groups:
        current_layout = group.layout
        if not isinstance(current_layout, Floating):
            if current_layout.margin > 6:
                current_layout.margin -= 5
                if hasattr(current_layout, "single_margin"):
                    current_layout.single_margin -= 5
            group.layout_all()
    # bar = qtile.current_screen.top
    # margin = bar.margin
    # margin = [margin - 5] * 4 if not isinstance(margin, list) else [m - 5 for m in margin]
    # bar._configure(qtile, qtile.current_screen, reconfigure=True)
    # bar.draw()


@lazy.function
def suspend_toggle(_qtile):
    p = subprocess.run(
        ["sudo", "suspend-toggle"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    message = p.stdout.decode().strip()
    notify2.Notification(summary="Suspend toggle", message=message).show()


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


def check_if_process_running(process_name):
    """
    Check if there is any running process that contains the given name processName.
    """
    # Iterate over the all the running process
    for proc in psutil.process_iter():
        with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Check if process name contains the given name string.
            if process_name.lower() in proc.name().lower():
                return True
    return False
