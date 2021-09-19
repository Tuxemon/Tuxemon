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
from __future__ import annotations
from tuxemon.event import get_npc, MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class NPCAtCondition(EventCondition):
    """
    Check to see if a character is at the condition position on the map.

    Script usage:
        .. code-block::

            is npc_at <character>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").

    """

    name = "npc_at"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if a character is at the condition position on the map.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the chosen character is in the condition position.

        """
        player = get_npc(session, condition.parameters[0])
        if not player:
            return False

        # Get the condition's rectangle area. If we're on a tile in that area,
        # then this condition should return True.
        area_x = range(condition.x, condition.x + condition.width)
        area_y = range(condition.y, condition.y + condition.height)

        # If the player is at the coordinates and the operator is set to true
        # then return true
        return (
            round(player.tile_pos[0]) in area_x
            and round(player.tile_pos[1]) in area_y
        )
