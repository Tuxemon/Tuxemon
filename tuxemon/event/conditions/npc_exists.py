# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
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
        return get_npc(session, condition.parameters[0]) is not None
