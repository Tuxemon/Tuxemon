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
class CharAtPositionCondition(EventCondition):
    """
    Check to see if the character is at the position on the map.

    Script usage:
        .. code-block::

            is char_at_position <character>,<tile_pos_x>,<tile_pos_y>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        tile_pos_x: X position to set the character to.
        tile_pos_y: Y position to set the character to.
    """

    name: ClassVar[str] = "char_at_position"
    character: str
    tile_pos_x: int
    tile_pos_y: int

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False
        tile_pos = (self.tile_pos_x, self.tile_pos_y)
        return character.tile_pos == tile_pos
