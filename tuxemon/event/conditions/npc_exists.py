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
from tuxemon.states.world.worldstate import WorldState
from tuxemon.session import Session


class NPCExistsCondition(EventCondition):
    """
    Check to see if a character object exists in the current list of NPCs.

    Script usage:
        .. code-block::

            is npc_exists <character>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").

    """

    name = "npc_exists"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if a particular character exists.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the chosen character exists.

        """
        world = session.client.get_state_by_name(WorldState)

        return get_npc(session, condition.parameters[0]) is not None
