# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition
from tuxemon.map.map import get_coords, get_direction
from tuxemon.platform.const.sizes import SURFACE_KEYS

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class FacingTileCondition(CoreCondition):
    """
    Checks whether the player is currently facing a specific type of tile.

    **Parameters**
    - ``facing_tile``: The tile slug or surface key to check against.

    **Returns**
    - ``True`` if the player is facing a tile of the given type.
    - ``False`` otherwise.

    **Example**

    .. code-block:: json

        "conditions": [
            "is facing_tile water"
        ]
    """

    name = "facing_tile"
    facing_tile: str

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        player = session.player
        client = session.client

        tiles = get_coords(player.tile_pos, client.map_manager.map_size)

        label = (
            client.terrain_manager.get_all_tile_properties(self.facing_tile)
            if self.facing_tile in SURFACE_KEYS
            else client.collision_manager.check_collision_zones(
                client.map_manager.collision_map, self.facing_tile
            )
        )
        tiles = list(set(tiles).intersection(label))
        tile_locations = {
            get_direction(player.tile_pos, coords) for coords in tiles
        }
        return player.facing in tile_locations
