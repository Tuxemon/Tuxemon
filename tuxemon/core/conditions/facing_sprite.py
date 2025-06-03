# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition
from tuxemon.event import get_npc_pos
from tuxemon.map import get_coords, get_direction

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class FacingSpriteCondition(CoreCondition):
    """
    Checks if the player is facing a specific sprite.
    (eg. maniac, swimmer, log)
    """

    name = "facing_sprite"
    sprite: str

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        player = session.player
        client = session.client
        tiles = get_coords(player.tile_pos, client.map_manager.map_size)

        facing_directions = {
            get_direction(player.tile_pos, npc.tile_pos)
            for coords in tiles
            if (npc := get_npc_pos(session, coords))
            and npc.template.sprite_name == self.sprite
        }

        return player.facing in facing_directions
