# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class CharFacingCondition(EventCondition):
    """
    Check to see where a character is facing.

    Script usage:
        .. code-block::

            is char_facing <character>,<direction>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        direction: One of "up", "down", "left" or "right".

    """

    name = "char_facing"

    def test(self, session: Session, condition: MapCondition) -> bool:
        character = get_npc(session, condition.parameters[0])
        if character is None:
            logger.error(f"{condition.parameters[0]} not found")
            return False
        facing = condition.parameters[1]

        return character.facing == facing
