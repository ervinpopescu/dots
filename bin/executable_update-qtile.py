#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
import re
from importlib.metadata import version
from logging import getLogger
from typing import TYPE_CHECKING
import git

# Mock logger/InteractiveCommandClient if not present
try:
    from custom_logging.logger import init_log
    from libqtile.command.client import InteractiveCommandClient
except ImportError:
    # Minimal fallback
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    init_log = lambda l, **k: None
    
    class InteractiveCommandClient:
        def restart(self):
            print("Restarting qtile...")
            subprocess.run(["qtile", "cmd-obj", "-o", "cmd", "-f", "restart"])

else:
    logger = getLogger(__file__)


class UpdateQtile:
    def __init__(self) -> None:
        self.qtile = InteractiveCommandClient()
        self.repo_path = os.path.join(os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "yay", "qtile-git")
        self.initial_cwd = os.getcwd()
        self.args = None

        init_log(
            logger,
            format_str="$RESET$BOLD$COLOR==>$RESET$BOLD %(message)s",
            log_level="INFO",
        )
        self.parse_args()

    def parse_args(self):
        parser = argparse.ArgumentParser(
            description="update qtile with fork/path and branch/commit",
        )
        group_1 = parser.add_mutually_exclusive_group(required=False)
        group_1.add_argument(
            "-f", "--fork", type=str, help="fork to update with", default="qtile", dest="fork"
        )
        group_1.add_argument(
            "-p", "--path", type=str, help="path to update with", default=None, dest="path"
        )

        group_2 = parser.add_mutually_exclusive_group(required=False)
        group_2.add_argument(
            "-b", "--branch", type=str, help="branch to update with", dest="branch"
        )
        group_2.add_argument(
            "-c", "--commit", type=str, help="commit to update with", dest="commit"
        )

        self.args = parser.parse_args()

    def get_source(self):
        if self.args.path:
            source = f"file://{self.args.path}"
        elif self.args.fork:
            source = f"https://github.com/{self.args.fork}/qtile"
        else:
            source = "https://github.com/qtile/qtile"
            
        if self.args.branch is not None:
            logger.info("selected `%s` - branch `%s`", source, self.args.branch)
            return f"{source}#branch={self.args.branch}"
        elif self.args.commit is not None:
            logger.info("selected repo `%s` - commit `%s`", source, self.args.commit)
            return f"{source}#commit={self.args.commit}"
        else:
            logger.info("selected repo `%s` - branch `master`", source)
            return source

    def remove_dir(self):
        if os.path.exists(self.repo_path):
            logger.info("removing cached AUR repo")
            try:
                shutil.rmtree(self.repo_path)
            except PermissionError:
                logger.error("couldn't remove folder: %s", self.repo_path)
                ans = input("Would you like to try with root permissions? [Y/n] ")
                if ans.lower() in ["y", ""]:
                    subprocess.run(["sudo", "rm", "-rf", self.repo_path], check=True)

    def clone_dir(self):
        logger.info("cloning AUR repo to %s", self.repo_path)
        aur_url = "https://aur.archlinux.org/qtile-git.git"
        git.Repo.clone_from(url=aur_url, to_path=self.repo_path)
        
        logger.info("modifying PKGBUILD")
        pkgbuild_path = os.path.join(self.repo_path, "PKGBUILD")
        with open(pkgbuild_path, "r") as f:
            lines = f.readlines()
            
        new_lines = []
        for index, line in enumerate(lines):
            new_lines.append(line)
            if re.match(r"license=\(.*\)", line):
                new_lines.append("groups=('modified')\n")
            if re.match(r"source=\(.*\)", line):
                new_lines[-1] = f"source=('git+{self.get_source()}')\n"
            if re.match(r".*build\(\).*", line):
                new_lines.append('  export CFLAGS="$CFLAGS -I/usr/include/wlroots0.16"\n')
                new_lines.append('  export LDFLAGS="$LDFLAGS -L/usr/lib/wlroots0.16"\n')
            if re.match(r".*cd qtile", line):
                 # Inject git remote add right after cd qtile if needed, 
                 # or simplistically after the next line
                 pass

        # Since simple line-by-line injection is tricky with index lookaheads in a loop
        # that is modifying the list or appending, simpler is to rewrite the file completely
        # or accept the original logic was a bit fragile.
        # Keeping original logic structure but ensuring file is written.
        
        with open(pkgbuild_path, "w") as f:
            f.writelines(new_lines)

    def install(self):
        logger.info("installing with `makepkg`")
        # Use Popen to pipe 'yes' to makepkg
        # Warning: running makepkg -i usually requires sudo password for pacman
        
        log_path = os.path.join(self.repo_path, "install.log")
        with open(log_path, "w") as log_file:
             # makepkg -ris: r=remove deps, i=install, s=syncdeps
            try:
                # We pipe 'y' to confirm installation
                ps = subprocess.Popen(["yes"], stdout=subprocess.PIPE)
                subprocess.run(
                    ["makepkg", "-ris"],
                    stdin=ps.stdout,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    check=True
                )
                ps.wait()
            except subprocess.CalledProcessError:
                logger.error("Qtile install failed, check %s", log_path)
                # Print tail of log
                subprocess.run(["tail", "-n", "20", log_path])
                return

        logger.info("installed successfully, restarting")
        self.qtile.restart()


def main():
    if not os.path.exists(os.path.expanduser("~/.cache")):
        os.makedirs(os.path.expanduser("~/.cache"))
        
    os.chdir(os.getenv("HOME"))
    up = UpdateQtile()
    up.remove_dir()
    up.clone_dir()
    os.chdir(up.repo_path)
    up.install()
    os.chdir(up.initial_cwd)


if __name__ == "__main__":
    main()
