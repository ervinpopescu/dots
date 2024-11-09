import contextlib
import json
import subprocess

import notify2
import psutil

# from libqtile.backend.base import Window
from libqtile.bar import Bar
from libqtile.core.manager import Qtile
from libqtile.layout.floating import Floating
from libqtile.lazy import lazy

from modules.settings import settings

ms = settings["margin_size"]
group_layouts = [group["layout"] for group in settings["groups"].values()]
MARGIN_SIZE_DELTA = ms


@lazy.function
def window_to_prev_group(qtile: Qtile):
    i = qtile.groups.index(qtile.current_group)
    if qtile.current_window is not None and i != 0:
        qtile.current_window.togroup(qtile.groups[i - 1].name)
        qtile.current_screen.toggle_group(qtile.groups[i - 1])  # type: ignore


@lazy.function
def window_to_next_group(qtile: Qtile):
    i = qtile.groups.index(qtile.current_group)
    if qtile.current_window is not None and i != 6:
        qtile.current_window.togroup(qtile.groups[i + 1].name)
        qtile.current_screen.toggle_group(qtile.groups[i + 1])  # type: ignore


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
                group.layout_all()  # type: ignore


@lazy.function
def groupbox_disable_drag(qtile: Qtile):
    widget = qtile.widgets_map["groupbox"]
    widget.disable_drag = widget.disable_drag is not True  # type: ignore


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
        for group, layout in zip(groups, group_layouts):
            group.setlayout(layout)


@lazy.function
def set_layout_current(qtile: Qtile):
    """toggle layout for current group between max and default"""
    groups = list(qtile.groups_map.keys())
    groups.pop()
    current_layout = qtile.current_screen.group.eval("self.layout.name")[1]
    current_group = qtile.current_screen.group.info()["name"]
    current_group_index = groups.index(current_group)  # type: ignore
    if current_layout == "max":
        qtile.current_screen.group.setlayout(group_layouts[current_group_index])  # type: ignore
    else:
        qtile.current_screen.group.setlayout("max")


@lazy.function
def toggle_gaps(qtile: Qtile):
    bars = [x for x in qtile.current_screen.gaps if isinstance(x, Bar)]
    groups = qtile.groups
    for group in groups:
        current_layout = group.layout
        if hasattr(current_layout, "margin"):
            if current_layout.margin != 0:
                current_layout.margin = 0
                if hasattr(current_layout, "single_margin"):
                    current_layout.single_margin = 0
                for bar in bars:
                    bar.margin = [0] * 4  # type: ignore
                    bar._configure(qtile, qtile.current_screen, reconfigure=True)
                    bar.draw()
            else:
                current_layout.margin = ms
                if hasattr(current_layout, "single_margin"):
                    current_layout.single_margin = ms
                for bar in bars:
                    bar.margin = [0, ms, ms, ms]
                    bar._configure(qtile, qtile.current_screen, reconfigure=True)
                    bar.draw()
            group.layout_all()


@lazy.function
def increase_gaps(qtile: Qtile):
    groups = qtile.groups
    for group in groups:
        current_layout = group.layout
        if not isinstance(current_layout, Floating):
            if isinstance(current_layout.margin, int):
                if current_layout.margin > 0 and current_layout.margin <= 100:
                    current_layout.margin += MARGIN_SIZE_DELTA
                    if hasattr(current_layout, "single_margin"):
                        current_layout.single_margin += MARGIN_SIZE_DELTA
            elif isinstance(current_layout.margin, list):
                if all(m > 0 for m in current_layout.margin) and all(
                    m <= 100 for m in current_layout.margin
                ):
                    margin = current_layout.margin
                    to_be_set_margin = []
                    for m in margin:
                        m += MARGIN_SIZE_DELTA
                        to_be_set_margin.append(m)
                    current_layout.margin = to_be_set_margin
                    to_be_set_margin = []
                    if hasattr(current_layout, "single_margin"):
                        for m in current_layout.single_margin:
                            m += MARGIN_SIZE_DELTA
                            to_be_set_margin.append(m)
                    current_layout.single_margin = to_be_set_margin
            group.layout_all()

    # bar = qtile.current_screen.bottom
    # margin = bar.margin  # type: ignore
    # logger.info("margin before set: %s", bar.margin)  # type: ignore
    # to_be_set_margin = []
    # if isinstance(margin, int):
    #     if margin > MARGIN_SIZE_DELTA:
    #         to_be_set_margin = [
    #             0,
    #             margin + MARGIN_SIZE_DELTA,
    #             margin + MARGIN_SIZE_DELTA,
    #             margin + MARGIN_SIZE_DELTA,
    #         ]
    # elif isinstance(margin, list):
    #     for i in margin:
    #         logger.info("%s", i)
    #         if i != 0:
    #             if i <= 100:
    #                 logger.info(f"i < 100, appending {i+MARGIN_SIZE_DELTA}")
    #                 to_be_set_margin.append(i + MARGIN_SIZE_DELTA)
    #             else:
    #                 return
    #         else:
    #             to_be_set_margin.append(0)
    # logger.info("to_be_set_margin: %s", to_be_set_margin)
    # bar.margin = to_be_set_margin  # type: ignore
    # logger.info("margin after set: %s", bar.margin)  # type: ignore
    # bar._configure(qtile, qtile.current_screen, reconfigure=True)  # type: ignore
    # bar.draw()  # type: ignore


@lazy.function
def decrease_gaps(qtile: Qtile):
    groups = qtile.groups
    for group in groups:
        current_layout = group.layout
        if not isinstance(current_layout, Floating):
            if isinstance(current_layout.margin, int):
                if current_layout.margin > MARGIN_SIZE_DELTA + 1:
                    current_layout.margin -= MARGIN_SIZE_DELTA
                    if hasattr(current_layout, "single_margin"):
                        current_layout.single_margin -= MARGIN_SIZE_DELTA
            elif isinstance(current_layout.margin, list):
                if all(m > MARGIN_SIZE_DELTA + 1 for m in current_layout.margin):
                    margin = current_layout.margin
                    to_be_set_margin = []
                    for m in margin:
                        m -= MARGIN_SIZE_DELTA
                        to_be_set_margin.append(m)
                    current_layout.margin = to_be_set_margin
                    to_be_set_margin = []
                    if hasattr(current_layout, "single_margin"):
                        for m in current_layout.single_margin:
                            m -= MARGIN_SIZE_DELTA
                            to_be_set_margin.append(m)
                    current_layout.single_margin = to_be_set_margin
            group.layout_all()

    # bar = qtile.current_screen.bottom
    # margin = bar.margin  # type: ignore
    # logger.info("margin before set: %s", bar.margin)  # type: ignore
    # to_be_set_margin = []
    # if isinstance(margin, int):
    #     if margin > MARGIN_SIZE_DELTA:
    #         to_be_set_margin = [
    #             0,
    #             margin - MARGIN_SIZE_DELTA,
    #             margin - MARGIN_SIZE_DELTA,
    #             margin - MARGIN_SIZE_DELTA,
    #         ]
    # elif isinstance(margin, list):
    #     for i in margin:
    #         logger.info("%s", i)
    #         if i >= MARGIN_SIZE_DELTA + 1:
    #             logger.info(f"i > MARGIN_SIZE_DELTA, appending {i-MARGIN_SIZE_DELTA}")
    #             to_be_set_margin.append(i - MARGIN_SIZE_DELTA)
    #         elif i <= 0:
    #             logger.info("i <= 0, appending 0")
    #             to_be_set_margin.append(0)
    #         else:
    #             return
    # logger.info("to_be_set_margin: %s", to_be_set_margin)
    # bar.margin = to_be_set_margin  # type: ignore
    # logger.info("margin after set: %s", bar.margin)  # type: ignore
    # bar._configure(qtile, qtile.current_screen, reconfigure=True)  # type: ignore
    # bar.draw()  # type: ignore


@lazy.function
def suspend_toggle(_):
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
        with contextlib.suppress(
            psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess
        ):
            # Check if process name contains the given name string.
            if process_name.lower() in proc.name().lower():
                return True
    return False
