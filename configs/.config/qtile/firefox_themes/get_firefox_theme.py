#!/usr/bin/python -u

# Note that running python with the `-u` flag is required on Windows,
# in order to ensure that stdin and stdout are opened in binary, rather
# than text, mode.

import json
import struct
import sys

import pyinotify

# Change this to the absolute path to firefox theme
FIREFOX_THEME_PATH = "/home/ervin/.config/qtile/firefox_themes/firefox_theme.json"


# Read a message from stdin and decode it.
def get_message():
    raw_length = sys.stdin.buffer.read(4)

    if not raw_length:
        sys.exit(0)
    message_length = struct.unpack("=I", raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode("utf-8")
    return json.loads(message)


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


class ModHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, evt):
        with open(FIREFOX_THEME_PATH) as f:
            data = json.load(f)
            send_message(encode_message(data))


with open(FIREFOX_THEME_PATH) as f:
    data = json.load(f)
    send_message(encode_message(data))

handler = ModHandler()
wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm, handler)
wdd = wm.add_watch(FIREFOX_THEME_PATH, pyinotify.IN_CLOSE_WRITE)
notifier.loop()
