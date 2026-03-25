# import asyncio
import json
import os

from libqtile import hook, qtile
from libqtile.backend.base.window import Window

from libqtile.ipc import Client
from libqtile.log_utils import logger
from libqtile.utils import create_task, get_cache_dir

from modules.settings import config_path

focus_history: list[Window] = []
excluded_focus_history = ["scratchpad", "qalttab"]  # for instance, scratchpads
focus_index = 0
last_focused_index = None
message = {}
reloaded = False

CACHE_DIR = get_cache_dir()
SOCKET_PATH = os.path.join(CACHE_DIR, "qalttab.wayland-0")
SAVED_HISTORY_PATH = os.path.join(config_path, "json", "focus_history.json")

def save_focus_history(qtile):
    global message
    with open(
        SAVED_HISTORY_PATH,
        "w",
    ) as f:
        json.dump(
            message,
            f,
        )


def load_focus_history(qtile):
    global message, reloaded
    with open(
        SAVED_HISTORY_PATH,
        "r",
    ) as f:
        message = json.load(f)
    if os.path.exists(SOCKET_PATH):
        client = Client(socket_path=SOCKET_PATH, is_json=True)
        create_task(
            client.async_send(message),
        ).add_done_callback(check_response)  # type: ignore
    reloaded = True


@hook.subscribe.user("alt_release")  # type: ignore
def alt_release():
    logger.debug(
        "---------------------- user_alt_release | reset_focus_index ----------------------"
    )
    logger.debug([win.get_wm_class() for win in focus_history])
    logger.debug(excluded_focus_history)
    logger.debug(focus_index)
    logger.debug(last_focused_index)

    reset_focus_index()
    all_windows = qtile.windows_map
    qalttab_win: Window = None  # type: ignore
    for wid in all_windows:
        if hasattr(all_windows[wid], "name"):
            if all_windows[wid].name == "qalttab":
                qalttab_win = all_windows[wid]
    if qalttab_win:
        qalttab_win.hide()
        focus_history[focus_index].group.focus(focus_history[focus_index], warp=True)  # type: ignore


@hook.subscribe.client_focus
def record_focus(window):
    global focus_history, message, reloaded

    logger.debug("---------------------- client_focus ----------------------")
    logger.debug(window)
    logger.debug([win.get_wm_class() for win in focus_history])
    logger.debug(excluded_focus_history)
    logger.debug(focus_index)
    logger.debug(last_focused_index)

    if (
        window.group
        and window.group.name not in excluded_focus_history
        and not any(ex in window.name for ex in excluded_focus_history)
    ):
        if window in focus_history:
            focus_history.remove(window)
        focus_history.insert(0, window)

    if not reloaded:
        message = {
            "message_type": "client_focus",
            "windows": [
                {
                    "class": win.get_wm_class()[0]  # type: ignore
                    if win.get_wm_class() is not None
                    else "not set",
                    "id": str(win.wid),
                    "name": win.name,
                    "group_name": win.group.name,  # type: ignore
                    "group_label": win.group.label,  # type: ignore
                }
                for win in focus_history
            ],
        }

        # write focus_history to qalttab socket
        if os.path.exists(SOCKET_PATH) and not any(ex in window.name for ex in excluded_focus_history):
            client = Client(socket_path=SOCKET_PATH, is_json=True)
            create_task(
                client.async_send(message),
            ).add_done_callback(check_response)  # type: ignore

        all_windows = qtile.windows_map
        qalttab_win: Window = None  # type: ignore

        for wid in all_windows:
            if hasattr(all_windows[wid], "name"):
                if all_windows[wid].name == "qalttab":
                    qalttab_win = all_windows[wid]
        if qalttab_win and qtile.current_window != qalttab_win:
            qalttab_win.hide()
        reloaded = False


def check_response(response):
    logger.debug(response.result())
    return


def cycle_windows(qtile):
    global focus_index, last_focused_index, message, focus_history, reloaded

    logger.debug("---------------------- cycle_windows ----------------------")
    logger.debug([win.get_wm_class() for win in focus_history])
    logger.debug(excluded_focus_history)
    logger.debug(focus_index)
    logger.debug(last_focused_index)

    if not focus_history:
        return

    focus_history[:] = [
        win
        for win in focus_history
        if win.group.name not in excluded_focus_history  # type: ignore
    ]

    if not focus_history:
        return

    if focus_index == -1:
        focus_index = len(focus_history) - 1
    else:
        focus_index = (focus_index + 1) % len(focus_history)

    if focus_index == 0:
        focus_index = last_focused_index if last_focused_index is not None else 0  # type: ignore

    next_window = focus_history[focus_index]

    if next_window == qtile.current_window:
        focus_index = (focus_index + 1) % len(focus_history)
        next_window = focus_history[focus_index]

    # qtile.current_screen.set_group(next_window.group)
    next_window.group.focus(next_window, warp=False)  # type: ignore
    next_window.bring_to_front()  # To get a scratchpad possibly hidden behind a newly maximized window.

    if not reloaded:
        message = {
            "message_type": "cycle_windows",
            "windows": [
                {
                    "class": win.get_wm_class()[0]  # type: ignore
                    if win.get_wm_class() is not None
                    else "not set",
                    "id": str(win.wid),
                    "name": win.name,
                    "group_name": win.group.name,  # type: ignore
                    "group_label": win.group.label,  # type: ignore
                }
                for win in focus_history
            ],
        }

        if (
            os.path.exists(SOCKET_PATH)
            and not any(ex in next_window.name for ex in excluded_focus_history)
        ):
            client = Client(socket_path=SOCKET_PATH, is_json=True)
            create_task(
                client.async_send(message),
            ).add_done_callback(check_response)  # type: ignore

        all_windows = qtile.windows_map
        qalttab_win: Window = None  # type: ignore

        for wid in all_windows:
            if hasattr(all_windows[wid], "name"):
                if all_windows[wid].name == "qalttab":
                    qalttab_win = all_windows[wid]

        if qalttab_win:
            logger.debug(qalttab_win)
            # qalttab_win.togroup(next_window.group.name)  # type: ignore
            qalttab_win.group.focus(qalttab_win, warp=True)  # type: ignore
            qalttab_win.bring_to_front()

        last_focused_index = focus_index
        reloaded = False


def reset_focus_index():
    global focus_index

    focus_index = 0


@hook.subscribe.group_window_remove
def remove_from_focus_history(group, window):
    global focus_history

    logger.debug(
        "---------------------- group_window_remove | remove_from_focus_history ----------------------"
    )
    logger.debug(window)
    logger.debug(group)
    logger.debug([win.get_wm_class() for win in focus_history])
    logger.debug(excluded_focus_history)
    logger.debug(focus_index)
    logger.debug(last_focused_index)

    if (
        not any(ex in window.name for ex in excluded_focus_history)
        and window.group.name not in excluded_focus_history
    ):
        focus_history.remove(window)


@hook.subscribe.client_killed
def remove_from_history(window):
    global focus_index

    logger.debug(
        "---------------------- client_killed | remove_from_history ----------------------"
    )
    logger.debug(window)
    logger.debug([win.get_wm_class() for win in focus_history])
    logger.debug(excluded_focus_history)
    logger.debug(focus_index)
    logger.debug(last_focused_index)

    if window in focus_history:
        focus_history.remove(window)

    if hasattr(window, "floating"):
        if window.floating:
            return  # Easiest workaround to handle internal pop-ups conflicts.

    if False:
        return

    if len(focus_history) >= 2:
        focus_index = 1
        next_window = focus_history[focus_index]
        # qtile.current_screen.set_group(next_window.group)
        next_window.group.focus(next_window, warp=False)  # type: ignore
    elif focus_history:
        focus_index = 0
        next_window = focus_history[focus_index]
        # qtile.current_screen.set_group(next_window.group)
        next_window.group.focus(next_window, warp=False)  # type: ignore
    else:
        focus_index = -1
