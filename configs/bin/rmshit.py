#! /usr/bin/env python3

import glob
import os
import shutil

globs = [
    # "~/Matlab*",
    "~/java.*",
    "~/.local/share/gegl-*",
]

shittyglobs = []

for g in globs:
    shittyglobs.extend(glob.glob(os.path.expanduser(g)))

shittyfiles = [
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
    *shittyglobs,
]


def yesno(question, default="y"):
    """Asks the user for YES or NO, always case insensitive.
    Returns True for YES and False for NO.
    """
    prompt = f"{question} (Y/n) "

    ans = input(prompt).strip().lower() or default

    return ans == "y"


def rmshit():
    found = []
    for f in shittyfiles:
        absf = os.path.expanduser(f)
        if os.path.exists(absf):
            found.append(absf)
            print(f"    {f}")

    if not found:
        print("No shitty files found :)")
        return

    if yesno("Remove all?", default="y"):
        for f in found:
            if os.path.isfile(f):
                os.remove(f)
            else:
                shutil.rmtree(f)
        print("All cleaned")
    else:
        print("No file removed")


if __name__ == "__main__":
    rmshit()
