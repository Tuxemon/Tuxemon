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
from __future__ import absolute_import

import logging

from core.components.event.eventcondition import EventCondition

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class PlayerFacingTileCondition(EventCondition):
    """ Checks to see if an NPC is facing a tile position
    """
    name = "player_facing_tile"

    def test(self, game, condition):
        """Checks to see the player is facing a tile position

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        **Examples:**

        >>> condition.__dict__
        {
            "type": "player_facing_tile",
            "parameters": [],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 6,
            "y": 9,
            ...
        }

        """

        coordinates = (condition.x, condition.y)
        tile_location = None

        # Next, we check the player position and see if we're one tile away from
        # the tile.
        if coordinates[1] == game.player1.tile_pos[1]:
            # Check to see if the tile is to the left of the player
            if coordinates[0] == game.player1.tile_pos[0] - 1:
                logger.debug("Tile is to the left of the player")
                tile_location = "left"
            # Check to see if the tile is to the right of the player
            elif coordinates[0] == game.player1.tile_pos[0] + 1:
                logger.debug("Tile is to the right of the player")
                tile_location = "right"

        if coordinates[0] == game.player1.tile_pos[0]:
            # Check to see if the tile is above the player
            if coordinates[1] == game.player1.tile_pos[1] - 1:
                logger.debug("Tile is above the player")
                tile_location = "up"
            elif coordinates[1] == game.player1.tile_pos[1] + 1:
                logger.debug("Tile is below the player")
                tile_location = "down"

        # Then we check to see if we're facing the Tile
        if game.player1.facing == tile_location:
            return True
        else:
            return False
