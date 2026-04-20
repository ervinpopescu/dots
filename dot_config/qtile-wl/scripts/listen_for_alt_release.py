#!/usr/bin/env python3

import select
import subprocess


def notify_qtile():
    subprocess.run(
        ["qticc", "cmd-obj", "-f", "fire_user_hook", "-a", "alt_release"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def listen_for_alt_release():
    process = subprocess.Popen(
        ["libinput", "debug-events", "--show-keycodes"], stdout=subprocess.PIPE
    )

    poll = select.poll()
    poll.register(process.stdout, select.POLLIN)

    try:
        while True:
            if poll.poll(100):
                line = process.stdout.readline()
                if not line:
                    break
                decoded_line = line.decode("utf-8").strip()

                if (
                    any(word in decoded_line for word in ["KEY_LEFTALT", "KEY_RIGHTALT"])
                    and "released" in decoded_line
                ):
                    notify_qtile()
    except KeyboardInterrupt:
        process.terminate()


if __name__ == "__main__":
    listen_for_alt_release()
