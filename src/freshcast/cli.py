"""Command line of the project: ``freshcast train`` and ``freshcast forecast``."""

import argparse
import logging
import sys

logger = logging.getLogger("freshcast")


def build_parser() -> argparse.ArgumentParser:
    """Build the parser with the two commands and their arguments."""
    raise NotImplementedError("Zadanie 14.5")
    raise NotImplementedError("Zadanie 14.5")


def main(argv: list[str] | None = None) -> int:
    """Run a command and return the process exit code.

    0 means success. 2 means the run could not start because the settings
    file is missing or invalid. Any other failure is a bug or bad data: it
    is logged with its traceback and the exit code is 1.
    """
    raise NotImplementedError("Zadanie 14.5")
    raise NotImplementedError("Zadanie 14.5")


if __name__ == "__main__":
    sys.exit(main())
