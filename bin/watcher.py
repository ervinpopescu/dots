#!/bin/python

import time

from libqtile.command.client import InteractiveCommandClient
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

c = InteractiveCommandClient()


class Watcher(Observer):
    DIRECTORY_TO_WATCH = "/home/ervin/.config/qtile/"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
            print("RuntimeError")

        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):

        null_ls_condition = event.src_path.split("/")[-1].startswith(".null-ls")
        cpython_condition = "cpython" in event.src_path.split("/")[-1]
        if event.is_directory:
            return None

        elif (
            event.event_type == "created"
            and not null_ls_condition
            and not cpython_condition
        ):
            # Take any action here when a file is first created.
            print("Received created event - %s." % event.src_path)
            c.reload_config()

        elif (
            event.event_type == "modified"
            and not null_ls_condition
            and not cpython_condition
        ):
            # Taken any action here when a file is modified.
            print("Received modified event - %s." % event.src_path)
            c.reload_config()


if __name__ == "__main__":
    w = Watcher()
    w.run()
