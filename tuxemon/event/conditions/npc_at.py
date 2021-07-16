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

from tuxemon.event import get_npc
from tuxemon.event.eventcondition import EventCondition


class NPCAtCondition(EventCondition):
    """Checks to see if an npc is at a current position on the map."""

    name = "npc_at"

    def test(self, session, condition):
        """Checks to see if an npc is at a current position on the map.

        :param session: The session object
        :param condition: A dictionary of condition details. See :py:func:`map.Map.loadevents`
            for the format of the dictionary.

        :type session: tuxemon.session.Session
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False
        """
        player = get_npc(session, condition.parameters[0])
        if not player:
            return False

        # Get the condition's rectangle area. If we're on a tile in that area, then this condition
        # should return True.
        area_x = range(condition.x, condition.x + condition.width)
        area_y = range(condition.y, condition.y + condition.height)

        # If the player is at the coordinates and the operator is set to true then return true
        if round(player.tile_pos[0]) in area_x and round(player.tile_pos[1]) in area_y:
            return True

        # If the player is at the coordinates and the operator is set to false then return false
        else:
            return False
