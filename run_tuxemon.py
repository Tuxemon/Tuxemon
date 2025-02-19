#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from argparse import ArgumentParser

if __name__ == "__main__":
    from tuxemon import main, prepare

    config = prepare.CONFIG

    parser = ArgumentParser()
    parser.add_argument(
        "-m",
        "--mod",
        dest="mod",
        metavar="mymod",
        type=str,
        nargs="?",
        default=None,
        help="The mod directory used in the mods directory",
    )
    parser.add_argument(
        "-l",
        "--load",
        dest="slot",
        metavar="1,2,3",
        type=int,
        nargs="?",
        default=None,
        help="The index of the save file to load",
    )
    parser.add_argument(
        "-t",
        "--test-map",
        dest="test_map",
        type=str,
        nargs="?",
        default=None,
        help="Skip title screen and load map directly",
    )
    args = parser.parse_args()

    if args.mod:
        config.mods.insert(0, args.mod)
    if args.test_map:
        config.skip_titlescreen = True
        config.splash = False

    main.main(load_slot=args.slot)
