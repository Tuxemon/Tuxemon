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


class PlayerFacingNPCCondition(EventCondition):
    """ Checks to see the player is next to and facing a particular NPC
    """
    name = "player_facing_npc"

    def test(self, session,  condition):
        """ Checks to see the player is next to and facing a particular NPC

        :param session: The session object
        :param condition: A dictionary of condition details. See :py:func:`core.map.Map.loadevents`
            for the format of the dictionary.

        :type session: tuxemon.core.session.Session
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: slug

        **Examples:**

        >>> condition.__dict__
        {
            "type": "facing_npc",
            "parameters": [
                "npc_oak"
            ],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 0,
            "y": 0,
            ...
        }
        """
        npc_location = None

        npc = get_npc(session, condition.parameters[0])
        if not npc:
            return False

        # Next, we check the player position and see if we're one tile away from the NPC.
        if npc.tile_pos[1] == session.player.tile_pos[1]:
            # Check to see if the NPC is to the left of the player
            if npc.tile_pos[0] == session.player.tile_pos[0] - 1:
                logger.debug("NPC is to the left of the player")
                npc_location = "left"
            # Check to see if the NPC is to the right of the player
            elif npc.tile_pos[0] == session.player.tile_pos[0] + 1:
                logger.debug("NPC is to the right of the player")
                npc_location = "right"

        if npc.tile_pos[0] == session.player.tile_pos[0]:
            # Check to see if the NPC is above the player
            if npc.tile_pos[1] == session.player.tile_pos[1] - 1:
                logger.debug("NPC is above the player")
                npc_location = "up"
            elif npc.tile_pos[1] == session.player.tile_pos[1] + 1:
                logger.debug("NPC is below the player")
                npc_location = "down"

        # Then we check to see if we're facing the NPC
        if session.player.facing == npc_location:
            return True
        else:
            return False
