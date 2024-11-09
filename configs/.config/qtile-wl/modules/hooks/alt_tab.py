import asyncio
import os

from libqtile import hook, qtile
from libqtile.backend.base.window import Window
from libqtile.ipc import Client
from libqtile.log_utils import logger
from libqtile.utils import get_cache_dir

focus_history: list[Window] = []
excluded_focus_history = ["scratchpad", "qalttab"]  # for instance, scratchpads
focus_index = 0
last_focused_index = None

cache_dir = get_cache_dir()
socket_path = os.path.join(cache_dir, "qalttab.wayland-0")


@hook.subscribe.user("alt_release")  # type: ignore
def alt_release():
    logger.info(
        "---------------------- user_alt_release | reset_focus_index ----------------------"
    )
    logger.info([win.get_wm_class() for win in focus_history])
    logger.info(excluded_focus_history)
    logger.info(focus_index)
    logger.info(last_focused_index)

    all_windows = qtile.windows_map
    qalttab_win: Window = None  # type: ignore

    for wid in all_windows:
        if hasattr(all_windows[wid], "name"):
            if all_windows[wid].name == "qalttab":
                qalttab_win = all_windows[wid]
    if qalttab_win:
        qalttab_win.bring_to_front()
        qalttab_win.hide()

    reset_focus_index()


@hook.subscribe.client_focus
def record_focus(window):
    global focus_history

    # logger.info("---------------------- client_focus ----------------------")
    # logger.info([win.get_wm_class() for win in focus_history])
    # logger.info(excluded_focus_history)
    # logger.info(focus_index)
    # logger.info(last_focused_index)

    if (
        window.group
        and window.group.name not in excluded_focus_history
        and window.name not in excluded_focus_history
    ):
        if window in focus_history:
            focus_history.remove(window)
        focus_history.insert(0, window)

    # write focus_history to qalttab socket
    if os.path.exists(socket_path) and window.name not in excluded_focus_history:
        client = Client(socket_path=socket_path, is_json=True)
        asyncio.create_task(
            client.async_send(
                {
                    "message_type": "client_focus",
                    "windows": [
                        {
                            "class": win.get_wm_class()[0]  # type: ignore
                            if win.get_wm_class() is not None
                            else "not set",
                            "name": win.name,
                            "group_name": win.group.name,  # type: ignore
                            "group_label": win.group.label,  # type: ignore
                        }
                        for win in focus_history
                    ],
                }
            )
        ).add_done_callback(check_response)

    # hide qalttab window which is shown when it receives data
    all_windows = qtile.windows_map
    qalttab_win: Window = None  # type: ignore

    for wid in all_windows:
        if hasattr(all_windows[wid], "name"):
            if all_windows[wid].name == "qalttab":
                qalttab_win = all_windows[wid]
    # if qalttab_win and qtile.current_window != qalttab_win:
    #     qalttab_win.hide()


def check_response(response):
    # logger.info(response.result())
    return


def cycle_windows(qtile):
    global focus_index, last_focused_index

    logger.info("---------------------- cycle_windows ----------------------")
    logger.info([win.get_wm_class() for win in focus_history])
    logger.info(excluded_focus_history)
    logger.info(focus_index)
    logger.info(last_focused_index)

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

    qtile.current_screen.set_group(next_window.group)
    next_window.group.focus(next_window, warp=False)  # type: ignore

    if os.path.exists(socket_path) and next_window.name not in excluded_focus_history:
        client = Client(socket_path=socket_path, is_json=True)
        asyncio.create_task(
            client.async_send(
                {
                    "message_type": "cycle_windows",
                    "windows": [
                        {
                            "class": win.get_wm_class()[0]  # type: ignore
                            if win.get_wm_class() is not None
                            else "not set",
                            "name": win.name,
                            "group_name": win.group.name,  # type: ignore
                            "group_label": win.group.label,  # type: ignore
                        }
                        for win in focus_history
                    ],
                }
            )
        ).add_done_callback(check_response)

    all_windows = qtile.windows_map
    qalttab_win: Window = None  # type: ignore

    for wid in all_windows:
        if hasattr(all_windows[wid], "name"):
            if all_windows[wid].name == "qalttab":
                qalttab_win = all_windows[wid]

    if qalttab_win:
        logger.info(qalttab_win)
        qalttab_win.togroup(next_window.group.name)  # type: ignore
        qalttab_win.group.focus(qalttab_win, warp=True)  # type: ignore
        qalttab_win.bring_to_front()

    # next_window.bring_to_front()  # To get a scratchpad possibly hidden behind a newly maximized window.

    last_focused_index = focus_index


def reset_focus_index():
    global focus_index

    focus_index = 0


@hook.subscribe.group_window_remove
def remove_from_focus_history(group, window):
    global focus_history

    logger.info(
        "---------------------- group_window_remove | remove_from_focus_history ----------------------"
    )
    logger.info([win.get_wm_class() for win in focus_history])
    logger.info(excluded_focus_history)
    logger.info(focus_index)
    logger.info(last_focused_index)

    focus_history.remove(window)


@hook.subscribe.client_killed
def remove_from_history(window):
    global focus_index

    logger.info(
        "---------------------- client_killed | remove_from_history ----------------------"
    )
    logger.info([win.get_wm_class() for win in focus_history])
    logger.info(excluded_focus_history)
    logger.info(focus_index)
    logger.info(last_focused_index)

    if window in focus_history:
        focus_history.remove(window)

    if hasattr(window, "floating"):
        if window.floating:
            return  # Easiest workaround to handle internal pop-ups conflicts.

    if len(focus_history) >= 2:
        focus_index = 1
        next_window = focus_history[focus_index]
        qtile.current_screen.set_group(next_window.group)
        next_window.group.focus(next_window, warp=False)  # type: ignore
    elif focus_history:
        focus_index = 0
        next_window = focus_history[focus_index]
        qtile.current_screen.set_group(next_window.group)
        next_window.group.focus(next_window, warp=False)  # type: ignore
    else:
        focus_index = -1
