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
excluded_groups = ["scratchpad", "qalttab"]  # group names to exclude
excluded_wm_classes = ["qalttab"]  # wm_class values to exclude
focus_index = 0
last_focused_index = None
message: dict[str, object] = {}
reloaded = False

CACHE_DIR = get_cache_dir()
SOCKET_PATH = os.path.join(CACHE_DIR, "qalttab.wayland-0")
SAVED_HISTORY_PATH = os.path.join(config_path, "json", "focus_history.json")


def _is_excluded(window):
    """Check if a window should be excluded from focus history."""
    if window.group is None:
        return True
    if window.group.name in excluded_groups:
        return True
    # Check if window belongs to a ScratchPad (even when toggled to current group)
    for group in qtile.groups:
        if hasattr(group, "dropdowns") and any(
            dd.window == window for dd in group.dropdowns.values() if dd.window is not None
        ):
            return True
    wm_class = window.get_wm_class()
    if wm_class and wm_class[0] in excluded_wm_classes:
        return True
    return False


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
    global focus_index
    logger.debug("user_alt_release | focus_index=%s", focus_index)

    if focus_history and 0 <= focus_index < len(focus_history):
        next_window = focus_history[focus_index]
        qtile.current_screen.set_group(next_window.group)
        next_window.group.focus(next_window, warp=True)  # type: ignore
        next_window.bring_to_front()

    reset_focus_index()


@hook.subscribe.client_focus
def record_focus(window):
    global focus_history, message, reloaded

    logger.warning("record_focus: %s (group=%s) | history=%s",
                   window.name, window.group.name if window.group else None,
                   [(w.name, w.group.name if w.group else None) for w in focus_history])

    if not _is_excluded(window):
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
        if os.path.exists(SOCKET_PATH) and not _is_excluded(window):
            client = Client(socket_path=SOCKET_PATH, is_json=True)
            create_task(
                client.async_send(message),
            ).add_done_callback(check_response)  # type: ignore

        reloaded = False


def check_response(response):
    logger.debug(response.result())
    return


def cycle_windows(qtile):
    global focus_index, last_focused_index, message, focus_history, reloaded

    logger.warning("cycle_windows called | focus_index=%s last_focused=%s history=%s",
                   focus_index, last_focused_index,
                   [(w.name, w.group.name if w.group else None) for w in focus_history])

    if not focus_history:
        logger.warning("cycle_windows: empty focus_history, returning")
        return

    focus_history[:] = [
        win for win in focus_history
        if not _is_excluded(win)
    ]

    if not focus_history:
        logger.warning("cycle_windows: empty after filter, returning")
        return

    logger.warning("cycle_windows: after filter history=%s",
                   [(w.name, w.group.name if w.group else None) for w in focus_history])

    if focus_index == -1:
        focus_index = len(focus_history) - 1
    else:
        focus_index = (focus_index + 1) % len(focus_history)

    if focus_index >= len(focus_history):
        focus_index = 0

    next_window = focus_history[focus_index]

    logger.warning("cycle_windows: selected %s (index=%s)", next_window.name, focus_index)

    if not reloaded:
        message = {
            "message_type": "cycle_windows",
            "focus_index": focus_index,
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

        if os.path.exists(SOCKET_PATH) and not _is_excluded(next_window):
            logger.warning("cycle_windows: sending IPC message")
            client = Client(socket_path=SOCKET_PATH, is_json=True)
            create_task(
                client.async_send(message),
            ).add_done_callback(check_response)  # type: ignore
        else:
            logger.warning("cycle_windows: SKIPPED IPC (socket=%s, excluded=%s)",
                           os.path.exists(SOCKET_PATH), _is_excluded(next_window))

        last_focused_index = focus_index
        reloaded = False


def reset_focus_index():
    global focus_index

    focus_index = 0


@hook.subscribe.group_window_remove
def remove_from_focus_history(group, window):
    global focus_history

    if not _is_excluded(window) and window in focus_history:
        focus_history.remove(window)


@hook.subscribe.client_killed
def remove_from_history(window):
    global focus_index

    if window in focus_history:
        focus_history.remove(window)

    if hasattr(window, "floating"):
        if window.floating:
            return  # Easiest workaround to handle internal pop-ups conflicts.

    if len(focus_history) >= 2:
        focus_index = 1
        next_window = focus_history[focus_index]
        next_window.group.focus(next_window, warp=False)  # type: ignore
    elif focus_history:
        focus_index = 0
        next_window = focus_history[focus_index]
        next_window.group.focus(next_window, warp=False)  # type: ignore
    else:
        focus_index = -1
