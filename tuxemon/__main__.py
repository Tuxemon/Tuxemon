# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""Launches the game or headless server based on command-line arguments."""

import sys
from argparse import ArgumentParser, Namespace

from tuxemon.main import headless, main


def parse_args() -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description="Start the game or headless server.")
    parser.add_argument(
        "-s",
        "--headless",
        action="store_true",
        help="Run in headless mode (no graphical interface).",
    )
    return parser.parse_args()


def run() -> None:
    """Run the game or headless server based on parsed arguments."""
    try:
        args = parse_args()
        if args.headless:
            headless()
        else:
            main()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
