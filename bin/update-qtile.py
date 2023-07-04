#!/bin/python

import argparse
import os
import re
import shutil
import subprocess
from logging import getLogger

from custom_logging.logger import init_log
from git.repo import Repo


def main():
    cwd = os.getcwd()
    os.chdir(os.getenv("HOME"))
    logger = getLogger(__file__)
    init_log(
        logger,
        format_str="$RESET$BOLD$COLOR==>$RESET$BOLD %(message)s",
        log_level="INFO",
    )
    parser = argparse.ArgumentParser(
        description="update qtile with fork and branch",
        epilog="--commit and --branch are mutually exclusive",
    )
    parser.add_argument(
        "-m",
        "--maintainer",
        type=str,
        help="maintainer to pull",
        default="qtile",
        dest="maintainer",
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "-b",
        "--branch",
        type=str,
        help="branch to pull",
        dest="branch",
    )
    group.add_argument(
        "-c",
        "--commit",
        type=str,
        help="commit to pull",
        dest="commit",
    )
    args = parser.parse_args()
    logger.info(f"starting logging for {__file__}")

    qtile_repo_path = os.path.join(
        os.getenv("XDG_CACHE_HOME"), "yay", "qtile-git")
    if os.path.exists(qtile_repo_path):
        logger.info("removing cached qtile repo")
        shutil.rmtree(qtile_repo_path)

    aur_url = "https://aur.archlinux.org/qtile-git"
    if args.branch is not None:
        logger.info("installing qtile `%s` - branch `%s`",
                    args.maintainer, args.branch)
        github_url = f"https://github.com/{args.maintainer}/qtile#branch={args.branch}"
    elif args.commit is not None:
        logger.info(
            "installing qtile `%s` - commit `%s`",
            args.maintainer,
            args.commit,
        )
        github_url = f"https://github.com/{args.maintainer}/qtile#commit={args.commit}"
    else:
        logger.info("installing qtile `%s` - branch `master`", args.maintainer)
        github_url = f"https://github.com/{args.maintainer}/qtile"
    Repo.clone_from(url=aur_url, to_path=qtile_repo_path)
    with open(os.path.join(qtile_repo_path, "PKGBUILD"), "r") as f:
        lines = f.readlines()
    for index, line in enumerate(lines):
        if re.match(r"license=(.*)", line):
            lines.insert(index + 1, "groups=('modified')\n")
            lines.pop(index + 2)
        if re.match(r"source=(.*)", line):
            lines[index] = f"source=('git+{github_url}')\n"
    with open(os.path.join(qtile_repo_path, "PKGBUILD"), "w") as f:
        f.writelines(lines)
        f.close()

    os.chdir(qtile_repo_path)
    with subprocess.Popen("yes", stdout=subprocess.PIPE) as p:
        with open(os.path.join(qtile_repo_path, "install.log"), "w") as log_file:
            makepkg = subprocess.run(
                "makepkg -ris".split(),
                stdin=p.stdout,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
        try:
            makepkg.check_returncode()
        except subprocess.CalledProcessError:
            logger.error(
                "Qtile install failed, check in %s/install.log", qtile_repo_path
            )
    os.chdir(cwd)


if __name__ == "__main__":
    main()
