#!/bin/python

import os
import subprocess

bookmark = subprocess.check_output(["xclip", "-o"]).decode("utf-8")
print(bookmark)
file = os.path.join(os.path.expanduser("~"), ".local", "share", "bookmarks")


def notify_send(title, string):
    subprocess.run(
        ["notify-send", "-a", "bookmark", "-u", "normal", "-r", "42523", title, string]
    )


with open(file, "r") as f:
    bookmarks = f.readlines()

already_added = False
for i in range(len(bookmarks)):
    if bookmark in bookmarks[i]:
        notify_send("Oops", "Already bookmarked!")
        already_added = True

if not already_added:
    notify_send("Bookmark added", bookmark)
    bookmarks.append(bookmark + "\n")

with open(file, "w") as f:
    f.writelines(bookmarks)
