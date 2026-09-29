# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.map.map import get_coords, get_direction
from tuxemon.platform.const.sizes import SURFACE_KEYS
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CharFacingTileCondition(EventCondition):
    """
    Check to see if a character is facing a tile position.

    This is checked against all the tiles included in the condition object.

    Script usage:
        .. code-block::

            is char_facing_tile <character>[,value]

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        value: value (eg surfable) inside the tileset.
    """

    name: ClassVar[str] = "char_facing_tile"
    character: str
    value: str | None = None

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False

        current_box = session.current_condition_box
        if current_box is None:
            return False

        tiles = [
            (current_box.x + w, current_box.y + h)
            for w in range(0, current_box.width)
            for h in range(0, current_box.height)
        ]
        # get all the coordinates around the npc
        client = session.client
        npc_tiles = get_coords(character.tile_pos, client.map_manager.map_size)

        # check if the NPC is facing a specific set of tiles
        if self.value:
            if self.value in SURFACE_KEYS:
                label = client.terrain_manager.get_all_tile_properties(
                    self.value
                )
            else:
                label = client.collision_manager.check_collision_zones(
                    client.map_manager.collision_map, self.value
                )
            tiles = list(set(npc_tiles).intersection(label))

        # return common coordinates
        tiles = list(set(tiles).intersection(npc_tiles))
        tile_locations = {
            get_direction(character.tile_pos, coords) for coords in tiles
        }
        return character.facing in tile_locations
