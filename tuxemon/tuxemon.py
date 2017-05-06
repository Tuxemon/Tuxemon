#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
#
# tuxemon.py Main game
#
"""Starts the core.main.main() function which, in turn, initializes
pygame and starts the game, unless headless is specified.

To run an individual component (e.g. core/prepare.py):

`python -m core.prepare`

"""
import sys
import getopt


if __name__ == '__main__':
    server = False
    opts, args = getopt.getopt(sys.argv[1:], "hs", ["help", "server"])
    for opt, arg in opts:
        if opt == '-h':
            print(sys.argv[0], '[--server]')
            print("  -h              Display this help message")
            print("  -s, --headless  Start a headless server")
            sys.exit()
        elif opt in ("-s", "--server"):
            server = True

    if server:
        from core.main import headless
        headless()

    else:
        from core.main import main
        main()

    sys.exit()
