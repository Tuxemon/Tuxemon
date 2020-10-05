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

from tuxemon.core.event.eventcondition import EventCondition

logger = logging.getLogger(__name__)


class PlayerFacingTileCondition(EventCondition):
    """ Checks to see if an NPC is facing a tile position
    """
    name = "player_facing_tile"

    def test(self, session,  condition):
        """Checks to see the player is facing a tile position

        :param session: The session object
        :param condition: A dictionary of condition details. See :py:func:`core.map.Map.loadevents`
            for the format of the dictionary.

        :type session: tuxemon.core.session.Session
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

        tiles = [
            (condition.x + w, condition.y + h)
            for w in range(0, condition.width)
            for h in range(0, condition.height)
        ]
        tile_location = None

        # Next, we check the player position and see if we're one tile away from
        # the tile.
        for coordinates in tiles:
            if coordinates[1] == session.player.tile_pos[1]:
                # Check to see if the tile is to the left of the player
                if coordinates[0] == session.player.tile_pos[0] - 1:
                    logger.debug("Tile is to the left of the player")
                    tile_location = "left"
                # Check to see if the tile is to the right of the player
                elif coordinates[0] == session.player.tile_pos[0] + 1:
                    logger.debug("Tile is to the right of the player")
                    tile_location = "right"

            elif coordinates[0] == session.player.tile_pos[0]:
                # Check to see if the tile is above the player
                if coordinates[1] == session.player.tile_pos[1] - 1:
                    logger.debug("Tile is above the player")
                    tile_location = "up"
                elif coordinates[1] == session.player.tile_pos[1] + 1:
                    logger.debug("Tile is below the player")
                    tile_location = "down"

            # Then we check to see if we're facing the Tile
            if session.player.facing == tile_location:
                return True

        return False
