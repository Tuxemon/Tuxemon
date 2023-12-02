# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.db import Direction
from tuxemon.item.itemcondition import ItemCondition
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
        tiles = []
        tile_location = None

        # check if the NPC is facing a specific set of tiles
        world = client.get_state_by_name(WorldState)
        if self.facing_tile == "surfable":
            tiles = list(world.surfable_map)

        # Next, we check the player position and see if we're one tile
        # away from the tile.
        for coordinates in tiles:
            if coordinates[1] == player.tile_pos[1]:
                # Check to see if the tile is to the left of the player
                if coordinates[0] == player.tile_pos[0] - 1:
                    tile_location = Direction.left
                # Check to see if the tile is to the right of the player
                elif coordinates[0] == player.tile_pos[0] + 1:
                    tile_location = Direction.right

            elif coordinates[0] == player.tile_pos[0]:
                # Check to see if the tile is above the player
                if coordinates[1] == player.tile_pos[1] - 1:
                    tile_location = Direction.up
                elif coordinates[1] == player.tile_pos[1] + 1:
                    tile_location = Direction.down

            # Then we check to see if we're facing the Tile
            if player.facing == tile_location:
                return True

        return False
