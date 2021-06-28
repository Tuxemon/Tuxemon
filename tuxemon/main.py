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
# main Sets up the states and main game loop.
#
from __future__ import annotations
from typing import Optional
import logging

from tuxemon import log
from tuxemon import prepare
from tuxemon.player import Player
from tuxemon.session import local_session

logger = logging.getLogger(__name__)


def main(
    load_slot: Optional[int] = None,
) -> None:
    """
    Configure and start the game.

    Add all available states to our scene manager (:class:`tools.Client`)
    and start the game using the pygame interface.

    Parameters:
        load_slot: Number of the save slot to load, if any.

    """
    log.configure()
    prepare.init()
    config = prepare.CONFIG

    import pygame
    from tuxemon.client import Client

    client = Client(config.window_caption)
    client.auto_state_discovery()

    # global/singleton hack for now
    setattr(prepare, "GLOBAL_CONTROL", client)

    # load the player npc
    new_player = Player(config.player_npc)

    # WIP.  Will be more complete with game-view
    local_session.client = client
    local_session.player = new_player

    # background state is used to prevent other states from
    # being required to track dirty screen areas.  for example,
    # in the start state, there is a menu on a blank background,
    # since menus do not clean up dirty areas, the blank,
    # "Background state" will do that.  The alternative is creating
    # a system for states to clean up their dirty screen areas.
    if not config.skip_titlescreen:
        client.push_state("BackgroundState")
        client.push_state("StartState")

    if load_slot:
        client.push_state("LoadMenuState", load_slot=load_slot)
    elif config.splash:
        client.push_state("SplashState")
        client.push_state("FadeInTransition")

    # TODO: rename this to "debug map" or something
    if config.skip_titlescreen:
        state = client.push_state("WorldState")
        map_name = prepare.fetch("maps", prepare.CONFIG.starting_map)
        state.change_map(map_name)

    # block of code useful for testing
    if config.collision_map:
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


def headless() -> None:
    """Sets up out headless server and start the game."""
    from tuxemon.client import HeadlessClient

    control = HeadlessClient()
    control.auto_state_discovery()
    control.push_state("HeadlessServerState")
    control.main()
