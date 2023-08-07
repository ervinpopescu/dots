#!/bin/python

import os
import subprocess

bookmark = subprocess.check_output(["xclip", "-o"]).decode("utf-8")
print(bookmark)
file = os.path.join(os.path.expanduser("~"), ".local", "share", "bookmarks")


def dunstify(title, string):
    subprocess.run(
        ["dunstify", "-a", "bookmark", "-u", "normal", "-r", "42523", title, string]
    )


with open(file, "r") as f:
    bookmarks = f.readlines()

already_added = False
for i in range(len(bookmarks)):
    if bookmark in bookmarks[i]:
        dunstify("Oops", "Already bookmarked!")
        already_added = True

if not already_added:
    dunstify("Bookmark added", bookmark)
    bookmarks.append(bookmark + "\n")

with open(file, "w") as f:
    f.writelines(bookmarks)
