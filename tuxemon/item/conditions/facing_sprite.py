# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.event import get_npc_pos
from tuxemon.item.itemcondition import ItemCondition
from tuxemon.map import get_coords, get_direction

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class FacingSpriteCondition(ItemCondition):
    """
    Checks if the player is facing a specific sprite.
    (eg. maniac, swimmer, log)

    """

    name = "facing_sprite"
    sprite: str

    def test(self, target: Monster) -> bool:
        player = self.session.player
        client = self.session.client
        tiles = get_coords(player.tile_pos, client.map_size)

        for coords in tiles:
            npc = get_npc_pos(self.session, coords)
            if npc and npc.sprite_name == self.sprite:
                facing = get_direction(player.tile_pos, npc.tile_pos)
                return player.facing == facing

        return False
