# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class CharPositionAction(EventAction):
    """
    Set the position of a character.

    Script usage:
        char_position <character>,<tile_pos_x>,<tile_pos_y>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        tile_pos_x: X position to set the character to.
        tile_pos_y: Y position to set the character to.
    """

    name = "char_position"
    character: str
    tile_pos_x: int
    tile_pos_y: int

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        position = (self.tile_pos_x, self.tile_pos_y)
        if not character.world.boundary_checker.is_within_boundaries(position):
            raise ValueError(
                f"Character is outside the boundaries of the map at ({position[0]}, {position[1]})"
            )
        character.remove_collision()
        character.set_position(position)
