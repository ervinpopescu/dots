#!/usr/bin/python -u

# Note that running python with the `-u` flag is required on Windows,
# in order to ensure that stdin and stdout are opened in binary, rather
# than text, mode.

import contextlib
import json
import os
import shutil
import struct
import sys
import tempfile

import pyinotify

IN_CLOSE_WRITE = getattr(pyinotify, "IN_CLOSE_WRITE")

# Change this to the absolute path to firefox theme
FIREFOX_THEME_PATH = os.path.expanduser(
    "~/.config/qtile/firefox_themes/firefox_theme.json"
)


def initialize_firefox_theme():
    source = os.path.expanduser("~/.config/qtile/firefox_themes/themes/catppuccin.json")
    destination_dir = os.path.dirname(FIREFOX_THEME_PATH)
    temporary_path = None
    try:
        with open(source, "rb") as source_file:
            with tempfile.NamedTemporaryFile(
                dir=destination_dir, delete=False
            ) as temporary:
                temporary_path = temporary.name
                shutil.copyfileobj(source_file, temporary)
                temporary.flush()
                os.fsync(temporary.fileno())
        os.link(temporary_path, FIREFOX_THEME_PATH)
    except FileExistsError:
        return
    finally:
        if temporary_path is not None:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary_path)


initialize_firefox_theme()


# Read a message from stdin and decode it.
def get_message():
    raw_length = sys.stdin.buffer.read(4)

    if not raw_length:
        sys.exit(0)
    message_length = struct.unpack("=I", raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode("utf-8")
    try:
        return json.loads(message)
    except json.JSONDecodeError:
        sys.exit(1)


# Encode a message for transmission, given its content.
def encode_message(message_content):
    encoded_content = json.dumps(message_content).encode("utf-8")
    encoded_length = struct.pack("=I", len(encoded_content))
    #  use struct.pack("10s", bytes), to pack a string of the length of 10 characters
    return {
        "length": encoded_length,
        "content": struct.pack(f"{len(encoded_content)}s", encoded_content),
    }


# Send an encoded message to stdout.
def send_message(encoded_message):
    sys.stdout.buffer.write(encoded_message["length"])
    sys.stdout.buffer.write(encoded_message["content"])
    sys.stdout.buffer.flush()


def load_firefox_theme():
    try:
        with open(FIREFOX_THEME_PATH) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("could not load Firefox theme") from error


class ModHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, evt):
        send_message(encode_message(load_firefox_theme()))


send_message(encode_message(load_firefox_theme()))

handler = ModHandler()
wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm, handler)
wdd = wm.add_watch(FIREFOX_THEME_PATH, IN_CLOSE_WRITE)
notifier.loop()
