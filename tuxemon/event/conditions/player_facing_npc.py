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

from tuxemon.event import get_npc
from tuxemon.event.eventcondition import EventCondition

logger = logging.getLogger(__name__)


class PlayerFacingNPCCondition(EventCondition):
    """Checks to see the player is next to and facing a particular NPC"""

    name = "player_facing_npc"

    def test(self, context, event, condition):
        """Checks to see the player is next to and facing a particular NPC

        :param event:
        :param context: The session object
        :param condition: A dictionary of condition details. See :py:func:`map.Map.loadevents`
            for the format of the dictionary.

        :type context: tuxemon.session.Session
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: slug
        """
        npc_location = None

        npc = get_npc(context, condition.parameters[0])
        if not npc:
            return False

        if npc.tile_pos[1] == context.player.tile_pos[1]:
            if npc.tile_pos[0] == context.player.tile_pos[0] - 1:
                logger.debug("NPC is to the left of the player")
                npc_location = "left"
            elif npc.tile_pos[0] == context.player.tile_pos[0] + 1:
                logger.debug("NPC is to the right of the player")
                npc_location = "right"

        if npc.tile_pos[0] == context.player.tile_pos[0]:
            if npc.tile_pos[1] == context.player.tile_pos[1] - 1:
                logger.debug("NPC is above the player")
                npc_location = "up"
            elif npc.tile_pos[1] == context.player.tile_pos[1] + 1:
                logger.debug("NPC is below the player")
                npc_location = "down"

        if context.player.facing == npc_location:
            return True
        else:
            return False
