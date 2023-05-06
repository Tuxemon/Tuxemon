# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple, Union

from tuxemon.event import get_npc_pos
from tuxemon.event.actions.remove_npc import RemoveNpcAction
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class RemoveEffectResult(TechEffectResult):
    pass


@dataclass
class RemoveEffect(TechEffect):
    """
    Removes the NPC and creates a variable.
    """

    name = "remove"

    def apply(
        self,
        tech: Technique,
        user: Union[Monster, None],
        target: Union[Monster, None],
    ) -> RemoveEffectResult:
        if target:
            return {"success": True}
        # using technique in the worldstate
        else:
            coords: Tuple[int, int] = (0, 0)
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
                return {"success": True}
            else:
                return {"success": False}
