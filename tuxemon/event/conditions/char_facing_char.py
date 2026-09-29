# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.map.map import get_coords, get_direction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CharFacingCharCondition(EventCondition):
    """
    Check to see the character is next to and facing a particular character.

    Script usage:
        .. code-block::

            is char_facing_char <character1>,<character2>

    Script parameters:
        character1: Either "player" or character slug name (e.g. "npc_maple").
        character2: Either "player" or character slug name (e.g. "npc_maple").
    """

    name: ClassVar[str] = "char_facing_char"
    character1: str
    character2: str

    def test(self, session: Session) -> bool:
        client = session.client
        npc_location = None

        character1 = session.client.get_npc(self.character1)
        character2 = session.client.get_npc(self.character2)
        if character2 is None or character1 is None:
            return False

        # get all the coordinates around the npc
        npc_tiles = get_coords(
            character2.tile_pos, client.map_manager.map_size
        )
        npc_location = get_direction(character1.tile_pos, character2.tile_pos)

        if character1.tile_pos in npc_tiles:
            logger.debug(
                f"{character1.name} is facing {npc_location} at {character2.slug}"
            )
            return character1.facing == npc_location

        return False
