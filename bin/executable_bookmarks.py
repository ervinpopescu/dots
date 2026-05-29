#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Optional dependency
try:
    from rofi import Rofi
except ImportError:
    print("Error: 'rofi' python module not found.", file=sys.stderr)
    sys.exit(1)

BOOKMARKS_FILE = Path.home() / ".local" / "share" / "bookmarks"

def main():
    if not shutil.which("rofi"):
        print("Error: rofi command not found.", file=sys.stderr)
        sys.exit(1)

    if not shutil.which("xdotool"):
        print("Error: xdotool command not found. Cannot type bookmark.", file=sys.stderr)
        sys.exit(1)

    if not BOOKMARKS_FILE.exists():
        print(f"No bookmarks file found at {BOOKMARKS_FILE}", file=sys.stderr)
        return

    with open(BOOKMARKS_FILE, "r") as f:
        bookmarks = [line.strip() for line in f.readlines() if line.strip()]

    if not bookmarks:
        print("No bookmarks found.", file=sys.stderr)
        return

    r = Rofi(lines=len(bookmarks))
    index, key = r.select("Select bookmark", bookmarks)

    if key == 0 and index != -1:
        # xdotool type ...
        subprocess.run(
            ["xdotool", "type", bookmarks[index]],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

if __name__ == "__main__":
    main()
