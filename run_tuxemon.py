#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from argparse import ArgumentParser, Namespace
import sys
from tuxemon import main, prepare


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Start the game or headless server.")
    parser.add_argument(
        "-m",
        "--mod",
        dest="mod",
        metavar="MOD_DIR",
        type=str,
        nargs="?",
        default=None,
        help="Specify a custom mod directory to use",
    )
    parser.add_argument(
        "-l",
        "--load",
        dest="slot",
        metavar="SAVE_SLOT",
        type=int,
        nargs="?",
        default=None,
        help="Load a saved game from the specified slot",
    )
    parser.add_argument(
        "-t",
        "--test-map",
        dest="test_map",
        type=str,
        nargs="?",
        default=None,
        help="Load a map directly (skipping title screen)",
    )
    parser.add_argument(
        "-s",
        "--headless",
        action="store_true",
        default=False,
        help="Run in headless mode (no graphical interface). Defaults to False.",
    )
    return parser.parse_args()

def launch_game() -> None:
    config = prepare.CONFIG

    try:
        args = parse_args()
        if args.mod:
            config.mods.insert(0, args.mod)
        if args.test_map:
            config.skip_titlescreen = True
            config.splash = False
        
        if args.headless:
            main.headless(config=config)
        else:
            main.main(config=config, load_slot=args.slot)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    launch_game()
