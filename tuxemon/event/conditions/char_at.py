# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.boundary import MapConditionBoundary
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

    name: ClassVar[str] = "char_at"
    character: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False

        if session.current_condition_box is None:
            return False

        map_boundary = MapConditionBoundary(session.current_condition_box)
        return map_boundary.is_within(character.tile_pos)
