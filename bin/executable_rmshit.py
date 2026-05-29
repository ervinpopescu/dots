#! /usr/bin/env python3

import glob
import os
import shutil
import sys
import argparse
from pathlib import Path

# Paths to clean (expanduser is handled later)
GLOBS = [
    "~/Matlab*",
    "~/java.*",
    "~/.local/share/gegl-*",
]

# Explicit files/dirs to remove
FILES = [
    "~/.ACEStream",
    "~/.FRD/links.txt",
    "~/.FRD/log/app.log",
    "~/.QtWebEngineProcess/",
    "~/.adobe",
    "~/.ansible/",
    "~/.asy/",
    "~/.bash_history",
    "~/.bazaar/",
    "~/.bzr.log",
    "~/.cmake/",
    "~/.config/enchant",
    "~/.cortex",
    "~/.dat.ngspice",
    "~/.dbus",
    "~/.distlib/",
    "~/.dropbox-dist",
    "~/.esd_auth",
    "~/.fehbg",
    "~/.fltk/",
    "~/.gconf",
    "~/.gconfd",
    "~/.gnome/",
    "~/.gnupg",
    "~/.gphoto",
    "~/.gstreamer-0.10",
    "~/.gtkrc-2.0",
    "~/.hplip",
    "~/.java/",
    "~/.jgmenu-lockfile",
    "~/.john",
    "~/.jssc/",
    "~/.lesshst",
    "~/.macromedia",
    "~/.mysql~/.npm/",
    "~/.nv/",
    "~/.npm/",
    "~/.nvidia-settings-rc",
    "~/.objectdb",
    "~/.octave_hist",
    "~/.oracle_jre_usage/",
    "~/.parallel",
    "~/.pulse",
    "~/.pylint.d/",
    "~/.python_history",
    "~/.qute_test/",
    "~/.qutebrowser/",
    "~/.recently-used",
    "~/.spicec",
    "~/.subversion/",
    "~/.texlive/",
    "~/.thumbnails",
    "~/.tox/",
    "~/.vim",
    "~/.viminfo",
    "~/.w3m/",
    "~/.wget-hsts",
    "~/.xsession-errors",
    "~/.xsession-errors.old",
    "~/.yarn",
    "~/.yarnrc",
    "~/.zsh_history",
    "~/SoftMaker",
    "~/ca2",
    "~/ca2~",
    "~/nvvp_workspace/",
    "~/octave-workspace",
    "~/unison.log",
]


def get_files_to_remove():
    """Collect all files to remove based on GLOBS and FILES lists."""
    found_files = []
    
    # Process globs
    for g in GLOBS:
        expanded = os.path.expanduser(g)
        found_files.extend(glob.glob(expanded))
        
    # Process explicit list
    for f in FILES:
        expanded = os.path.expanduser(f)
        if os.path.lexists(expanded):
            found_files.append(expanded)
            
    return sorted(list(set(found_files))) # Remove duplicates


def yesno(question, default="y"):
    """Asks the user for YES or NO."""
    prompt = f"{question} (Y/n) "
    ans = input(prompt).strip().lower() or default
    return ans == "y"


def main():
    parser = argparse.ArgumentParser(description="Remove unwanted 'shitty' files from home directory.")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    args = parser.parse_args()

    found = get_files_to_remove()

    if not found:
        print("No shitty files found :)")
        return

    print("Found the following files/directories:")
    for f in found:
        print(f"    {f}")

    if args.dry_run:
        print("\nDry run complete. No files removed.")
        return

    if args.yes or yesno("\nRemove all?", default="y"):
        count = 0
        for f in found:
            try:
                if os.path.isfile(f) or os.path.islink(f):
                    os.remove(f)
                elif os.path.isdir(f):
                    shutil.rmtree(f)
                count += 1
            except Exception as e:
                print(f"Error removing {f}: {e}", file=sys.stderr)
        print(f"All cleaned ({count} items removed).")
    else:
        print("No files removed.")


if __name__ == "__main__":
    main()
