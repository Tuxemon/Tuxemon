# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.platform.const.sizes import SURFACE_KEYS
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CharInCondition(EventCondition):
    """
    Check to see if the character is on a specific set of tiles.

    Script usage:
        .. code-block::

            is char_in <character>,<value>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple")
        value: value (eg surfable) inside the tileset.
    """

    name: ClassVar[str] = "char_in"
    character: str
    value: str

    def test(self, session: Session) -> bool:
        client = session.client
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False

        tiles = []
        if self.value in SURFACE_KEYS:
            tiles = client.terrain_manager.get_all_tile_properties(self.value)
        else:
            tiles = client.collision_manager.check_collision_zones(
                client.map_manager.collision_map, self.value
            )
        if tiles:
            return character.tile_pos in tiles
        return False
