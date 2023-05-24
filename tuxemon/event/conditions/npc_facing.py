# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class NPCFacingCondition(EventCondition):
    """
    Check to see where a character is facing.

    Script usage:
        .. code-block::

            is npc_facing <character>,<direction>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        direction: One of "up", "down", "left" or "right".

    """

    name = "npc_facing"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see where a character is facing.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the chosen character faces the chosen direction.

        """
        player = get_npc(session, condition.parameters[0])
        if not player:
            return False
        facing = condition.parameters[1]

        directions = ["up", "down", "left", "right"]
        if facing not in directions:
            logger.error(f"{facing} must be 'up', 'down', 'left' or 'right'")
            raise ValueError()
        else:
            return player.facing == facing
