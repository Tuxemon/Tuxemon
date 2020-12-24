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

    def test(self, context, event, condition):
        """Checks to see the player is facing a tile position

        :param event:
        :param context: The session object
        :param condition: A dictionary of condition details. See :py:func:`core.map.Map.loadevents`
            for the format of the dictionary.

        :type context: tuxemon.core.session.Session
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        """

        tiles = [
            (event.rect.left, event.rect.bottom)
            for w in range(0, event.rect.width)
            for h in range(0, event.rect.height)
        ]
        tile_location = None

        for coordinates in tiles:
            if coordinates[1] == context.player.tile_pos[1]:
                if coordinates[0] == context.player.tile_pos[0] - 1:
                    logger.debug("Tile is to the left of the player")
                    tile_location = "left"
                elif coordinates[0] == context.player.tile_pos[0] + 1:
                    logger.debug("Tile is to the right of the player")
                    tile_location = "right"

            elif coordinates[0] == context.player.tile_pos[0]:
                if coordinates[1] == context.player.tile_pos[1] - 1:
                    logger.debug("Tile is above the player")
                    tile_location = "up"
                elif coordinates[1] == context.player.tile_pos[1] + 1:
                    logger.debug("Tile is below the player")
                    tile_location = "down"

            if context.player.facing == tile_location:
                return True

        return False
