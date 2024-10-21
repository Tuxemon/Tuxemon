# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class CharPositionCondition(EventCondition):
    """
    Check to see if the character is at the position on the map.

    Script usage:
        .. code-block::

            is char_position <character>,<tile_pos_x>,<tile_pos_y>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        tile_pos_x: X position to set the character to.
        tile_pos_y: Y position to set the character to.

    """

    name = "char_position"

    def test(self, session: Session, condition: MapCondition) -> bool:
        character = get_npc(session, condition.parameters[0])
        if character is None:
            logger.error(f"{condition.parameters[0]} not found")
            return False
        tile_pos_x = int(condition.parameters[1])
        tile_pos_y = int(condition.parameters[2])
        tile_pos = (tile_pos_x, tile_pos_y)
        return character.tile_pos == tile_pos
