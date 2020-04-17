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
# core.main Sets up the states and main game loop.
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from tuxemon.core import prepare
from tuxemon.core.client import LocalPygameClient
from tuxemon.core.npc import NPC
from tuxemon.core.session import local_session
from tuxemon.core.world import World

logger = logging.getLogger(__name__)


def main(load_slot=None):
    """Add all available states to our scene manager (tools.Control)
    and start the game using the pygame interface.

    :rtype: None
    :returns: None

    """
    prepare.init()

    world = World()
    client = LocalPygameClient(world, prepare.CONFIG)

    # setup game for local single player
    player = NPC(prepare.CONFIG.player_npc)
    player.map_name = prepare.CONFIG.starting_map
    player.set_position((5, 5))
    world.add_entity(player)

    local_session.client = client
    local_session.world = world
    local_session.player = player

    client.push_state("BackgroundState")
    client.push_state("StartState")
    client.push_state("WorldState", world=world, player=player)

    # if load_slot:
    #     control.push_state("LoadMenuState", load_slot=load_slot)
    # elif prepare.CONFIG.splash:
    #     # Show the splash screen if it is enabled in the game configuration
    #     control.push_state("SplashState")
    #     control.push_state("FadeInTransition")

    client.run()
