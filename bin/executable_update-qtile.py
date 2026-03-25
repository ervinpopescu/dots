#!/bin/python


import argparse
import os
import re
import shutil
import subprocess
from importlib.metadata import version
from logging import getLogger
import textwrap
from typing import TYPE_CHECKING

import git
from custom_logging.logger import init_log
from libqtile.command.client import InteractiveCommandClient

logger = getLogger(__file__)


class UpdateQtile:
    def __init__(self) -> None:
        if TYPE_CHECKING:
            from libqtile.core.manager import Qtile

            self.qtile: Qtile

        self.qtile = InteractiveCommandClient()
        self.repo_path = os.path.join(os.getenv("XDG_CACHE_HOME"), "yay", "qtile-git")
        self.bare_repo: git.Repo
        self.initial_cwd = os.getcwd()
        self.args = None

        init_log(
            logger,
            format_str="$RESET$BOLD$COLOR==>$RESET$BOLD %(message)s",
            log_level="INFO",
        )
        self.parse_args()
        return

    def parse_args(self):
        parser = argparse.ArgumentParser(
            description="update qtile with fork/path and branch/commit",
        )
        group_1 = parser.add_mutually_exclusive_group(required=False)
        group_1.add_argument(
            "-f",
            "--fork",
            type=str,
            help="fork to update with",
            default="qtile",
            dest="fork",
        )
        group_1.add_argument(
            "-p",
            "--path",
            type=str,
            help="path to update with",
            default=None,
            dest="path",
        )

        group_2 = parser.add_mutually_exclusive_group(required=False)
        group_2.add_argument(
            "-b",
            "--branch",
            type=str,
            help="branch to update with",
            dest="branch",
        )
        group_2.add_argument(
            "-c",
            "--commit",
            type=str,
            help="commit to update with",
            dest="commit",
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

    # def version_check(self):
    #     git_commit = self.bare_repo.rev_parse("HEAD")
    #     git_date = git_commit.committed_datetime

    #     local_running_commit = self.bare_repo.rev_parse(
    #         re.sub(".*g", "", self.qtile.qtile_info()["version"])
    #     )
    #     local_running_date = local_running_commit.committed_datetime

    #     local_installed_commit = self.bare_repo.rev_parse(
    #         re.sub(".*g", "", version("qtile"))
    #     )
    #     local_installed_date = local_installed_commit.committed_datetime

    #     print(local_running_commit, "|", local_running_date)
    #     print(local_installed_commit, "|", local_installed_date)
    #     print(git_commit, "|", git_date)
    #     if self.args.commit is not None:
    #         if git_version != self.args.commit[:8]:
    #             return
    #     if git_version != local_installed:
    #         logger.info("git version is newer than installed, upgrading...")
    #         return
    #     else:
    #         if local_installed == local_running:
    #             logger.error(
    #                 "no need to upgrade, qtile is already updated to the latest version"
    #             )
    #             exit(0)
    #         else:
    #             logger.error("please restart qtile")
    #             exit(0)

    def remove_dir(self):
        if os.path.exists(self.repo_path):
            logger.info("removing cached AUR repo")
            try:
                shutil.rmtree(self.repo_path)
            except PermissionError:
                logger.error("couldn't remove folder")
                ans = input("Would you like to try with root permissions? [Y/n]")
                if ans in ["Y", "", "y"]:
                    subprocess.run(f"sudo rm -rf {self.repo_path}".split())

    def clone_dir(self):
        logger.info("cloning AUR repo")
        aur_url = "https://aur.archlinux.org/qtile-git"
        git.Repo.clone_from(url=aur_url, to_path=self.repo_path)
        logger.info("modifying PKGBUILD")
        with open(os.path.join(self.repo_path, "PKGBUILD"), "r") as f:
            lines = f.readlines()
            for index, line in enumerate(lines):
                if re.match(r"license=\(.*\)", line):
                    lines.insert(index + 1, "groups=('modified')\n")
                    # lines.pop(index + 2)
                if re.match(r"source=\(.*\)", line):
                    lines[index] = f"source=('git+{self.get_source()}')\n"
                if re.match(r".*build\(\).*", line):
                    lines.insert(
                        index + 1,
                        '  export CFLAGS="$CFLAGS -I/usr/include/wlroots0.16"\n',
                    )
                    lines.insert(
                        index + 2,
                        '  export LDFLAGS="$LDFLAGS -L/usr/lib/wlroots0.16"\n',
                    )
                if re.match(r".*cd qtile", line) and re.match(
                    ".*git describe", lines[index + 1]
                ):
                    lines.insert(
                        index + 1,
                        "  git remote add upstream https://github.com/qtile/qtile.git\n",
                    )
                    lines.insert(index + 2, "  git fetch upstream --tags\n")
        with open(os.path.join(self.repo_path, "PKGBUILD"), "w") as f:
            f.writelines(lines)
        return

    def install(self):
        logger.info("installing with `makepkg`")
        with subprocess.Popen("yes", stdout=subprocess.PIPE) as p:
            with open(os.path.join(self.repo_path, "install.log"), "w") as log_file:
                makepkg = subprocess.run(
                    "makepkg -ris".split(),
                    stdin=p.stdout,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                )
        try:
            makepkg.check_returncode()
            logger.info("installed successfully, restarting")
            self.qtile.restart()
            return
        except subprocess.CalledProcessError as e:
            logger.error(
                "Qtile install failed, check in `%s/install.log`\nError:\n%s",
                self.repo_path,
                e.output,
            )
            return


def main():
    os.chdir(os.getenv("HOME"))
    up = UpdateQtile()
    # up.version_check()
    up.remove_dir()
    up.clone_dir()
    os.chdir(up.repo_path)
    up.install()
    os.chdir(up.initial_cwd)


if __name__ == "__main__":
    main()
