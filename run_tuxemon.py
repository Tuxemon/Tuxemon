#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import TYPE_CHECKING

from tuxemon.log import get_git_hash
from tuxemon.user_config import CONFIG, TuxemonConfig

if TYPE_CHECKING:
    from tuxemon.prepare import DisplayContext

logger = logging.getLogger(__name__)


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Start the Tuxemon game or headless server."
    )

    parser.add_argument(
        "-m",
        "--mod",
        dest="mod",
        metavar="MOD_DIR",
        type=str,
        help="Specify a custom mod directory to use",
    )
    parser.add_argument(
        "-l",
        "--load",
        dest="slot",
        metavar="SAVE_SLOT",
        type=int,
        help="Load a saved game from the specified slot",
    )
    parser.add_argument(
        "-t",
        "--test-map",
        dest="test_map",
        metavar="MAP_NAME",
        type=str,
        help="Load a map directly (skipping title screen)",
    )
    parser.add_argument(
        "-s",
        "--headless",
        action="store_true",
        default=False,
        help="Run in headless mode (no graphical interface).",
    )

    return parser


def parse_args(argv: list[str] | None = None) -> Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.mod:
        mod_path = Path(args.mod)
        if not mod_path.exists() or not mod_path.is_dir():
            parser.error(
                f"Mod directory does not exist or is not a directory: {mod_path}"
            )

    return args


def init_display(platform: str = "pygame") -> DisplayContext:
    if platform == "pygame":
        from tuxemon.prepare import pygame_init

        return pygame_init()

    if platform == "headless":
        from tuxemon.prepare import headless_init

        return headless_init()

    raise ValueError(f"Unsupported platform: {platform}")


def apply_config_from_args(config: TuxemonConfig, args: Namespace) -> None:
    if args.mod:
        config.mods.insert(0, args.mod)

    if args.test_map:
        config.skip_titlescreen = True
        config.splash = False


def handle_fatal_error(e: Exception) -> None:
    import traceback

    error_msg = f"Tuxemon Error: {e}"
    full_error = f"{error_msg}\n\nTraceback:\n{traceback.format_exc()}"

    logger.error(full_error)

    try:
        error_log = Path.cwd() / "tuxemon_error.log"
        error_log.write_text(full_error, encoding="utf-8")
        print(f"Error details saved to: {error_log}", file=sys.stderr)
    except Exception:
        pass

    if sys.platform == "win32" and hasattr(sys, "frozen"):
        try:
            import ctypes

            msg = f"{error_msg}\n\nSee tuxemon_error.log for details."
            ctypes.windll.user32.MessageBoxW(0, msg, "Tuxemon Error", 1)
        except Exception:
            pass

    sys.exit(1)


def launch_game(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    from tuxemon.platform import platform

    platform.init()

    platform_mode = "headless" if args.headless else "pygame"
    context = init_display(platform_mode)

    print(get_git_hash())

    from tuxemon import main as tuxemon_main

    config = CONFIG.copy()
    config.logging.configure()

    try:
        apply_config_from_args(config, args)

        if args.headless:
            tuxemon_main.headless(config=config, context=context)
        else:
            tuxemon_main.main(
                config=config, context=context, load_slot=args.slot
            )

    except Exception as e:
        handle_fatal_error(e)


if __name__ == "__main__":
    launch_game()
