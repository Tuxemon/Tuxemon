# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition
from tuxemon.map import get_coords, get_direction
from tuxemon.prepare import SURFACE_KEYS
from tuxemon.states.world.worldstate import WorldState

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class FacingTileCondition(CoreCondition):
    """
    Checks if the player is facing specific tiles.

    """

    name = "facing_tile"
    facing_tile: str

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        player = session.player
        client = session.client

        tiles = get_coords(player.tile_pos, client.map_manager.map_size)

        world = client.get_state_by_name(WorldState)
        label = (
            world.get_all_tile_properties(
                client.map_manager.surface_map, self.facing_tile
            )
            if self.facing_tile in SURFACE_KEYS
            else world.check_collision_zones(
                client.map_manager.collision_map, self.facing_tile
            )
        )
        tiles = list(set(tiles).intersection(label))

        tile_location = next(
            (get_direction(player.tile_pos, coords) for coords in tiles), None
        )

        return player.facing == tile_location
