# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.event import get_npc_pos
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.map import get_coords, get_direction

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


@dataclass
class RemoveEffect(ItemEffect):
    """
    Removes the NPC and creates a variable.
    """

    name = "remove"

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> ItemEffectResult:
        remove: bool = False
        client = self.session.client
        player = self.session.player
        tiles = get_coords(player.tile_pos, client.map_size)

        for coords in tiles:
            npc = get_npc_pos(self.session, coords)
            if npc:
                facing = get_direction(player.tile_pos, npc.tile_pos)
                if player.facing == facing:
                    client.event_engine.execute_action(
                        "remove_npc", [npc.slug], True
                    )
                    player.game_variables[npc.slug] = self.name
                    remove = True

        return ItemEffectResult(
            name=item.name, success=remove, num_shakes=0, extras=[]
        )
