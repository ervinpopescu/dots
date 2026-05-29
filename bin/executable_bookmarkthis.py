#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
from pathlib import Path

BOOKMARKS_DIR = Path.home() / ".local" / "share"
BOOKMARKS_FILE = BOOKMARKS_DIR / "bookmarks"


def dunstify(title, string):
    if shutil.which("dunstify"):
        subprocess.run(
            ["dunstify", "-a", "bookmark", "-u", "normal", "-r", "42523", title, string],
            stderr=subprocess.DEVNULL
        )
    else:
        print(f"{title}: {string}")


def main():
    if not shutil.which("xclip"):
        dunstify("Error", "xclip not found")
        sys.exit(1)

    try:
        bookmark = subprocess.check_output(["xclip", "-o"]).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        dunstify("Error", "Failed to get content from clipboard")
        sys.exit(1)

    if not bookmark:
        dunstify("Error", "Clipboard is empty")
        sys.exit(1)

    print(f"Bookmarking: {bookmark}")

    # Ensure directory exists
    BOOKMARKS_DIR.mkdir(parents=True, exist_ok=True)

    bookmarks = []
    if BOOKMARKS_FILE.exists():
        with open(BOOKMARKS_FILE, "r") as f:
            bookmarks = [line.strip() for line in f.readlines()]

    if bookmark in bookmarks:
        dunstify("Oops", "Already bookmarked!")
    else:
        with open(BOOKMARKS_FILE, "a") as f:
            f.write(bookmark + "\n")
        dunstify("Bookmark added", bookmark)


if __name__ == "__main__":
    main()
