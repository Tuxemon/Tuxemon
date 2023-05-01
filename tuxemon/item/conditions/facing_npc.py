# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.event import get_npc
from tuxemon.item.itemcondition import ItemCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class FacingNpcCondition(ItemCondition):
    """
    Checks if the player is facing a NPC.

    """

    name = "facing_npc"
    npc_slug: str

    def test(self, target: Monster) -> bool:
        player = self.session.player
        npc_location = None
        npc = get_npc(self.session, self.npc_slug)
        if not npc:
            return False

        if npc.tile_pos[1] == player.tile_pos[1]:
            if npc.tile_pos[0] == player.tile_pos[0] - 1:
                npc_location = "left"
            elif npc.tile_pos[0] == player.tile_pos[0] + 1:
                npc_location = "right"

        if npc.tile_pos[0] == player.tile_pos[0]:
            if npc.tile_pos[1] == player.tile_pos[1] - 1:
                npc_location = "up"
            elif npc.tile_pos[1] == player.tile_pos[1] + 1:
                npc_location = "down"

        return player.facing == npc_location
