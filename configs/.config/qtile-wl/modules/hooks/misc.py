import contextlib

from libqtile import hook, qtile
from libqtile.core.manager import Qtile

qtile: Qtile

# @hook.subscribe.screen_change
# def change_wallpaper(event):
#     with open(os.path.expanduser("~/.local/share/wallpaper/log")) as f:
#         path = f.readlines()
#     if path is not None or path.len() != 0:
#         subprocess.call(f"run_wall_wl.sh {path} all".split())
#     else:
#         subprocess.call("run_wall_wl.sh rand all".split())
#     n_screens = len(qtile.get_screens())
#     if n_screens == 3 or n_screens == 1:
#         qtile.reconfigure_screens()
#         qtile.reload_config()


@hook.subscribe.client_killed
def switch_group(client):
    with contextlib.suppress(AttributeError):
        num_windows_in_group = len(client.group.info()["windows"])
        if num_windows_in_group == 0:
            qtile.current_screen.toggle_group(qtile.current_screen.previous_group)  # type: ignore
