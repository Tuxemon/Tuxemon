# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.event import get_npc_pos
from tuxemon.event.actions.remove_npc import RemoveNpcAction
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class RemoveEffectResult(ItemEffectResult):
    pass


@dataclass
class RemoveEffect(ItemEffect):
    """
    Removes the NPC and creates a variable.
    """

    name = "remove"

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> RemoveEffectResult:
        remove: bool = False
        coords: tuple[int, int] = (0, 0)
        player = self.session.player
        facing = player.facing
        player_x = player.tile_pos[0]
        player_y = player.tile_pos[1]
        if facing == "down":
            y = player_y - 1
            coords = player_x, y
        elif facing == "up":
            y = player_y + 1
            coords = player_x, y
        elif facing == "right":
            x = player_x + 1
            coords = x, player_y
        elif facing == "left":
            x = player_x - 1
            coords = x, player_y

        npc = get_npc_pos(self.session, coords)
        if npc:
            RemoveNpcAction(npc_slug=npc.slug).start()
            self.session.player.game_variables[npc.slug] = self.name
            remove = True
        return {"success": remove, "num_shakes": 0, "extra": None}
