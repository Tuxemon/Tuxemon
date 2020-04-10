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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from collections import namedtuple

logger = logging.getLogger(__name__)

# Set up map action and condition objects
condition_fields = [
    "type",
    "parameters",
    "x",
    "y",
    "width",
    "height",
    "operator",
    "name"]

action_fields = [
    "type",
    "parameters",
    "name"]

event_fields = [
    "id",
    "name",
    "x",
    "y",
    "w",
    "h",
    "conds",
    "acts"]

MapCondition = namedtuple("condition", condition_fields)
MapAction = namedtuple("action", action_fields)
EventObject = namedtuple("eventobject", event_fields)

__all__ = [
    "MapAction",
    "MapCondition",
    "get_npc"
]


def get_npc(game, slug):
    """ Gets an NPC object by slug.

    :param game: The main game object that contains all the game's variables.
    :param slug: The slug of the NPC that exists on the current map.

    :type game: tuxemon.core.control.Control
    :type slug: str

    :rtype: tuxemon.core.player.Player
    :returns: The NPC object or None if the NPC is not found.
    """
    if slug == "player":
        return game.player1

    # Loop through the NPC list and see if the slug matches any in the list
    world = game.get_state_name("WorldState")
    if world is None:
        logger.error("Cannot search for NPC if world doesn't exist: " + slug)
        return

    # logger.error("Unable to find NPC: " + slug)
    return world.get_entity(slug)
