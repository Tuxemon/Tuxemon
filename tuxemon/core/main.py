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
# core.main Sets up the states and main game loop.
#

import logging

from tuxemon.core import log
from tuxemon.core import prepare
from tuxemon.core.player import Player
from tuxemon.core.session import local_session

logger = logging.getLogger(__name__)


def main(load_slot=None):
    """Add all available states to our scene manager (tools.Client)
    and start the game using the pygame interface.

    :rtype: None
    :returns: None

    """
    log.configure()

    import pygame
    from tuxemon.core.client import Client

    prepare.init()
    client = Client(prepare.CONFIG.window_caption)
    client.auto_state_discovery()

    # global/singleton hack for now
    setattr(prepare, "GLOBAL_CONTROL", client)

    # load the player npc
    new_player = Player(prepare.CONFIG.player_npc)

    # WIP.  Will be more complete with game-view
    local_session.client = client
    local_session.player = new_player

    # background state is used to prevent other states from
    # being required to track dirty screen areas.  for example,
    # in the start state, there is a menu on a blank background,
    # since menus do not clean up dirty areas, the blank,
    # "Background state" will do that.  The alternative is creating
    # a system for states to clean up their dirty screen areas.
    client.push_state("BackgroundState")

    # basically the main menu
    client.push_state("StartState")

    if load_slot:
        client.push_state("LoadMenuState", load_slot=load_slot)
    elif prepare.CONFIG.splash:
        # Show the splash screen if it is enabled in the game configuration
        client.push_state("SplashState")
        client.push_state("FadeInTransition")

    # block of code useful for testing
    if prepare.CONFIG.collision_map:
        logger.info("********* DEBUG OPTIONS ENABLED *********")

        logging.basicConfig(level=logging.DEBUG)

        action = client.event_engine.execute_action

        action("add_monster", ("bigfin", 10))
        action("add_monster", ("dandylion", 10))

        action("add_item", ("potion",))
        action("add_item", ("cherry",))
        action("add_item", ("capture_device",))

        for i in range(10):
            action("add_item", ("super_potion",))

        for i in range(100):
            action("add_item", ("apple",))

    client.main()
    pygame.quit()


def headless():
    """Sets up out headless server and start the game.

    :rtype: None
    :returns: None

    """
    from tuxemon.core.client import HeadlessClient

    control = HeadlessClient()
    control.auto_state_discovery()
    control.push_state("HeadlessServerState")
    control.main()
