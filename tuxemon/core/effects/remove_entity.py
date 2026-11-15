# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.map.map import get_coords, get_direction

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session


@dataclass
class RemoveEntityEffect(CoreEffect):
    """
    Applies the "remove_entity" effect to an item.

    This effect removes a nearby NPC from the map if the player is facing
    them, and records the removal by setting a game variable with the NPC's
    slug. It is typically used for scripted events where interacting with
    an NPC causes them to disappear.

    **Example**

    .. code-block:: json

        "effects": [
            "remove_entity"
        ]
    """

    name = "remove_entity"

    def apply_item(self, session: Session, item: Item) -> ItemEffectResult:
        remove: bool = False
        client = session.client
        player = session.player
        tiles = get_coords(player.tile_pos, client.map_manager.map_size)

        for coords in tiles:
            npc = session.client.get_npc_pos(coords)
            if npc:
                facing = get_direction(player.tile_pos, npc.tile_pos)
                if player.facing == facing:
                    client.event_engine.execute_action(
                        "remove_npc", [npc.slug], True
                    )
                    player.game_variables.set(npc.slug, self.name)
                    remove = True

        return ItemEffectResult(name=item.name, success=remove)
