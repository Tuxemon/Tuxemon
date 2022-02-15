#!/usr/bin/env python3
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
# Leif Theden <leif.theden@gmail.com>
#
#
from argparse import ArgumentParser
from tuxemon.log import send_logs, popup_send_log_consent
import logging
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    from tuxemon import prepare, main
    config = prepare.CONFIG

    parser = ArgumentParser()
    parser.add_argument('-m', '--mod', dest='mod', metavar='mymod', type=str, nargs='?',
                        default=None, help='The mod directory used in the mods directory')
    parser.add_argument('-l', '--load', dest='slot', metavar='1,2,3', type=int, nargs='?',
                        default=None, help='The index of the save file to load')
    parser.add_argument('-s', '--starting-map', dest='starting_map', metavar='map.tmx', type=str, nargs='?',
                        default=None, help='The starting map')
    parser.add_argument('-t', '--test-map', dest='test_map', type=str, nargs='?',
                        default=None, help='Skip title screen and load map directly')
    args = parser.parse_args()

    if args.mod:
        config.mods.insert(0, args.mod)
    if args.starting_map:
        config.starting_map = args.starting_map
    if args.test_map:
        config.starting_map = args.test_map
        config.skip_titlescreen = True
        config.splash = False

    
    try:
        main.main(load_slot=args.slot)
    except Exception as ex:
        from pygame import quit as pg_quit
        pg_quit()
        logging.error("Exception occured", exc_info=True)
        if ex != KeyboardInterrupt and ex != EOFError:
            if popup_send_log_consent():
                send_logs()
            else:
                print("Not sending logs.")
