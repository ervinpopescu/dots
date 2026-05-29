#!/usr/bin/env python3

import sys
import time
from pathlib import Path

try:
    from libqtile.command.client import InteractiveCommandClient
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError as e:
    print(f"Error: Missing dependency ({e})", file=sys.stderr)
    sys.exit(1)

# Initialize Client safely
try:
    c = InteractiveCommandClient()
except Exception:
    print("Warning: Could not connect to Qtile client.", file=sys.stderr)
    c = None


class Watcher:
    DIRECTORY_TO_WATCH = Path.home() / ".config" / "qtile"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        if not self.DIRECTORY_TO_WATCH.exists():
            print(f"Error: Directory {self.DIRECTORY_TO_WATCH} does not exist.", file=sys.stderr)
            return

        event_handler = Handler()
        self.observer.schedule(event_handler, str(self.DIRECTORY_TO_WATCH), recursive=True)
        self.observer.start()
        print(f"Watching {self.DIRECTORY_TO_WATCH}...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
            print("\nStopping watcher...")
        except Exception as e:
            self.observer.stop()
            print(f"Error: {e}")

        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        filename = Path(event.src_path).name

        # Ignore temporary/cache files
        if filename.startswith(".null-ls") or "cpython" in filename or filename.endswith("~"):
            return None

        if event.event_type in ["created", "modified"]:
            print(f"Reloading config due to {event.event_type} event on {filename}")
            if c:
                try:
                    c.reload_config()
                except Exception as e:
                    print(f"Failed to reload config: {e}")


if __name__ == "__main__":
    w = Watcher()
    w.run()
