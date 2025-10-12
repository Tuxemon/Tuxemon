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
        import traceback
        error_msg = f"Tuxemon Error: {e}"
        full_error = f"{error_msg}\n\nTraceback:\n{traceback.format_exc()}"
        print(full_error)
        
        # Log error to file for debugging
        try:
            import os
            from pathlib import Path
            error_log = Path.cwd() / "tuxemon_error.log"
            with open(error_log, "w") as f:
                f.write(full_error)
            print(f"Error details saved to: {error_log}")
        except:
            pass
        
        # Show error dialog on Windows GUI builds
        if sys.platform == "win32" and hasattr(sys, "frozen"):
            try:
                import ctypes
                msg = f"{error_msg}\n\nSee tuxemon_error.log for details."
                ctypes.windll.user32.MessageBoxW(0, msg, "Tuxemon Error", 1)
            except:
                pass  # Fall back to console output only
        
        sys.exit(1)

if __name__ == "__main__":
    launch_game()
