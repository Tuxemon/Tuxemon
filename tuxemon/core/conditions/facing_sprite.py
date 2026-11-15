# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition
from tuxemon.map.map import get_coords, get_direction

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class FacingSpriteCondition(CoreCondition):
    """
    Checks whether the player is currently facing a specific sprite (e.g. NPC or object).

    **Parameters**
    - ``sprite``: The name of the sprite to check (e.g. ``maniac``, ``swimmer``, ``log``).

    **Returns**
    - ``True`` if the player is facing the given sprite.
    - ``False`` otherwise.

    **Example**

    .. code-block:: json

        "conditions": [
            "is facing_sprite maniac"
        ]
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
            if (npc := session.client.get_npc_pos(coords))
            and npc.appearance_manager.state.sprite_name == self.sprite
        }

        return player.facing in facing_directions
