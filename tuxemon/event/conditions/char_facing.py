# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
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

    name: ClassVar[str] = "char_facing"
    character: str
    direction: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False

        return character.facing == self.direction
