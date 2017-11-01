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
# core.main Sets up the states and main game loop.
#
from __future__ import absolute_import

import logging

from . import prepare
from .components import log

logger = logging.getLogger(__name__)


def main():
    """Add all available states to our scene manager (tools.Control)
    and start the game using the pygame interface.

    :rtype: None
    :returns: None

    """
    log.configure()

    import pygame
    from .control import PygameControl

    prepare.init()
    control = PygameControl(prepare.ORIGINAL_CAPTION)
    control.auto_state_discovery()

    # background state is used to prevent other states from
    # being required to track dirty screen areas.  for example,
    # in the start state, there is a menu on a blank background,
    # since menus do not clean up dirty areas, the blank,
    # "Background state" will do that.  The alternative is creating
    # a system for states to clean up their dirty screen areas.
    control.push_state("BackgroundState")

    # basically the main menu
    control.push_state("StartState")

    # Show the splash screen if it is enabled in the game configuration
    if prepare.CONFIG.splash == "1":
        control.push_state("SplashState")
        control.push_state("FadeInTransition")

    # block of code useful for testing
    if prepare.CONFIG.collision_map == "1":
        logger.info("********* DEBUG OPTIONS ENABLED *********")

        # TODO: fix this player/player1 issue
        control.player1 = prepare.player1
        action = control.event_engine.execute_action

        action("add_monster", ("txmn_bigfin", 10))
        action("add_monster", ("txmn_dandylion", 10))

        action("add_item", ("item_potion",))
        action("add_item", ("item_cherry",))
        action("add_item", ("item_capture_device",))

        for i in range(10):
            action("add_item", ("item_super_potion",))

        for i in range(100):
            action("add_item", ("item_apple",))

    control.main()
    pygame.quit()


def headless():
    """Sets up out headless server and start the game.

    :rtype: None
    :returns: None

    """
    from .control import HeadlessControl

    control = HeadlessControl()
    control.auto_state_discovery()
    control.push_state("HeadlessServerState")
    control.main()
