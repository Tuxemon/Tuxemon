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

from tuxemon.core.event import get_npc
from tuxemon.core.event.eventcondition import EventCondition

logger = logging.getLogger(__name__)


class NPCFacingTileCondition(EventCondition):
    """ Checks to see if an NPC is facing a tile position
    """
    name = "npc_facing_tile"

    def test(self, session,  condition):
        """ Checks to see if an NPC is facing a tile position

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
            "type": "facing_tile",
            "parameters": ["npc_maple"],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 6,
            "y": 9,
            ...
        }
        """
        # Get the npc object from the game.
        npc = get_npc(session, condition.parameters[0])
        if not npc:
            return False

        tiles = [
            (condition.x + w, condition.y + h)
            for w in range(0, condition.width)
            for h in range(0, condition.height)
        ]
        tile_location = None

        for coordinates in tiles:
            # Next, we check the npc position and see if we're one tile away from
            # the tile.
            if coordinates[1] == npc.tile_pos[1]:
                # Check to see if the tile is to the left of the npc
                if coordinates[0] == npc.tile_pos[0] - 1:
                    logger.debug("Tile is to the left of the NPC")
                    tile_location = "left"
                # Check to see if the tile is to the right of the npc
                elif coordinates[0] == npc.tile_pos[0] + 1:
                    logger.debug("Tile is to the right of the NPC")
                    tile_location = "right"

            if coordinates[0] == npc.tile_pos[0]:
                # Check to see if the tile is above the npc
                if coordinates[1] == npc.tile_pos[1] - 1:
                    logger.debug("Tile is above the NPC")
                    tile_location = "up"
                elif coordinates[1] == npc.tile_pos[1] + 1:
                    logger.debug("Tile is below the NPC")
                    tile_location = "down"

            # Then we check to see the npc is facing the Tile
            if npc.facing == tile_location:
                return True

        return False
