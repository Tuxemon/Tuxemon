# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.db import SurfaceKeys
from tuxemon.item.itemcondition import ItemCondition
from tuxemon.map import get_coords, get_direction
from tuxemon.states.world.worldstate import WorldState

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class FacingTileCondition(ItemCondition):
    """
    Checks if the player is facing specific tiles.

    """

    name = "facing_tile"
    facing_tile: str

    def test(self, target: Monster) -> bool:
        player = self.session.player
        client = self.session.client
        # get all the coordinates around the player
        tiles = get_coords(player.tile_pos, client.map_size)
        tile_location = None

        # check if the NPC is facing a specific set of tiles
        world = client.get_state_by_name(WorldState)
        if self.facing_tile in SurfaceKeys:
            label = world.get_all_tile_properties(
                world.surface_map, self.facing_tile
            )
        else:
            label = world.check_collision_zones(
                world.collision_map, self.facing_tile
            )
        tiles = list(set(tiles).intersection(label))

        # Next, we check the player position and see if we're one tile
        # away from the tile.
        for coords in tiles:
            tile_location = get_direction(player.tile_pos, coords)

        return player.facing == tile_location
