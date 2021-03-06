"""Entry point for linking dotfiles.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from . import log
from .link import Linker
from .resolver import Resolver
from .scan import Scanner
from .schema import DotfilesJson, PrettyPath


def _argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="links dotfiles")
    parser.add_argument(
        "-d",
        "--dotfiles",
        type=argparse.FileType("r"),
        help="The dotfiles.json file to load",
    )
    parser.add_argument(
        "-r", "--relative", action="store_true", help="Create relative links"
    )
    parser.add_argument(
        "-s", "--scan", action="store_true", help="Scan for untracked dotfiles",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Make output more verbose",
    )
    return parser


def _get_repo_root() -> Path:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        log.fatal(
            "Couldn't run `git` to determine repo root; pass --dotfiles explicitly."
        )
        sys.exit(1)

    if proc.returncode != 0:
        log.fatal("Couldn't get repo root from git; pass --dotfiles explicitly.")
        sys.exit(1)

    return Path(proc.stdout.strip())


def main() -> None:
    """Entry point.
    """
    args = _argparser().parse_args()

    repo_root = _get_repo_root()
    if args.dotfiles is None:
        dotfiles_path = open(repo_root / "dotfiles.json")
    else:
        dotfiles_path = args.dotfiles

    dotfiles = DotfilesJson.load_from_file(dotfiles_path)
    dotfiles_path.close()
    link_root = Path.home()
    resolver = Resolver(
        repo_root=repo_root, link_root=link_root, relative=args.relative
    )
    resolved = resolver.resolve_all(dotfiles)

    if args.scan:
        log.warn("Scanning for dotfiles is an experimental feature.")
        scanner = Scanner(link_root, resolved.ignored, resolved.dotfiles)
        for p in scanner.find_dotfiles():
            # TODO: Fill in scanner processing.
            # Actions:
            # - ignore the path
            # - move it to dotfiles
            #
            # Should also note if it's a directory or file.
            log.info(str(PrettyPath.from_path(p).disp))

    else:
        linker = Linker(verbose=args.verbose,)
        linker.link_all(resolved.dotfiles)


if __name__ == "__main__":
    main()
