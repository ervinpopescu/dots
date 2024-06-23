import psutil
import os

from libqtile import hook, qtile
from libqtile.backend.base import Window
from libqtile.core.manager import Qtile
from libqtile.log_utils import logger

from modules.session import Session

qtile: Qtile
session = Session()

# @hook.subscribe.startup
# def set_loglevel():
#     qtile.info()

@hook.subscribe.startup_once
def restore_session():
    apps = [app["exe"] for app in session.apps]
    logger.info("Restoring session with apps: %s", ",".join(apps))
    for app in apps:
        qtile.spawn(app)

@hook.subscribe.client_managed
def add_app_to_session(client: Window):
    wid = client.info()["id"]
    exe = psutil.Process(client.window.get_net_wm_pid()).exe()
    session.add_app(wid, exe)

@hook.subscribe.client_killed
def remove_app_from_session(client: Window):
    wid = client.info()["id"]
    session.remove_app(wid)

@hook.subscribe.shutdown
@hook.subscribe.user("save_session")
def save_session():
    session.save()

@hook.subscribe.user("get_session")
def log_session():
    session.log()

@hook.subscribe.user("set_session")
def set_session():
    session.from_windows()

@hook.subscribe.user("clear_session")
def clear_session():
    session.clear()
    if os.path.exists(session.save_path):
        os.remove(session.save_path)
