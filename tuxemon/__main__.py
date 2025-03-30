# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""Starts the main.main() function which, in turn, initializes
pygame and starts the game, unless headless is specified.
"""

import getopt
import sys


def main(args=None):
    server = False
    opts, args = getopt.getopt(sys.argv[1:], "hs", ["help", "server"])
    for opt, arg in opts:
        if opt == "-h":
            print(sys.argv[0], "[--server]")
            print("  -h              Display this help message.")
            print("  -s, --headless  Start a headless server.")
            sys.exit()
        elif opt in ("-s", "--server"):
            server = True

    if server:
        from tuxemon.main import headless

        headless()

    else:
        from tuxemon.main import main

        main()

    sys.exit()


if __name__ == "__main__":
    main()
