# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import logging

logger = logging.getLogger(__name__)


def get_npc(game, slug):
    """ Gets an NPC object by slug.

    :param game: The main game object that contains all the game's variables.
    :param slug: The slug of the NPC that exists on the current map.

    :type game: core.control.Control
    :type slug: Str

    :rtype: core.components.player.Npc
    :returns: The NPC object or None if the NPC is not found.

    """
    # Loop through the NPC list and see if the slug matches any in the list
    world = game.get_state_name("WorldState")
    if not world:
        logger.error("Cannot search for NPC if  world doesn't exist: " + slug)
        return

    if slug in world.npcs:
        return world.npcs[slug]

    logger.error("Unable to find NPC: " + slug)
    return
