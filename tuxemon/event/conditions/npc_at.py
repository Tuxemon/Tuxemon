# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition, collide, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class NPCAtCondition(EventCondition):
    """
    Check to see if a character is at the condition position on the map.

    Script usage:
        .. code-block::

            is npc_at [character]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        Default "player".

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
        slug = (
            "player" if not condition.parameters else condition.parameters[0]
        )
        npc = get_npc(session, slug)
        if not npc:
            return False
        return collide(condition, npc.tile_pos)
