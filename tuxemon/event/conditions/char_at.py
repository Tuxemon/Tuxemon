# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.boundary import MapConditionBoundary
from tuxemon.db import SpatialCondition
from tuxemon.event import get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CharAtCondition(EventCondition):
    """
    Check to see if the character is at the condition position on the map.

    Script usage:
        .. code-block::

            is char_at [character]

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
    """

    name = "char_at"

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        character = get_npc(session, condition.parameters[0])
        if character is None:
            logger.error(f"{condition.parameters[0]} not found")
            return False

        map_boundary = MapConditionBoundary(condition)
        return map_boundary.is_within(character.tile_pos)
