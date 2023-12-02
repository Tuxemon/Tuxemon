# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.db import Direction
from tuxemon.event import get_npc_pos
from tuxemon.item.itemcondition import ItemCondition

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
        coords: tuple[int, int] = (0, 0)
        player = self.session.player
        facing = player.facing
        player_x = player.tile_pos[0]
        player_y = player.tile_pos[1]
        if facing == Direction.down:
            y = player_y - 1
            coords = player_x, y
        elif facing == Direction.up:
            y = player_y + 1
            coords = player_x, y
        elif facing == Direction.right:
            x = player_x + 1
            coords = x, player_y
        elif facing == Direction.left:
            x = player_x - 1
            coords = x, player_y

        npc = get_npc_pos(self.session, coords)
        if npc:
            if npc.sprite_name == self.sprite:
                return True
            else:
                return False
        else:
            return False
