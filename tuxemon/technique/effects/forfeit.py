# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import set_var
from tuxemon.db import OutputBattle
from tuxemon.locale import T
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class ForfeitEffectResult(TechEffectResult):
    pass


@dataclass
class ForfeitEffect(TechEffect):
    """
    Forfeit allows player to forfeit.

    """

    name = "forfeit"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> ForfeitEffectResult:
        combat = tech.combat_state
        player = user.owner
        assert combat and player
        set_var(self.session, "battle_last_result", self.name)
        set_var(self.session, "teleport_clinic", OutputBattle.lost.value)
        combat._run = True
        params = {"npc": combat.players[1].name.upper()}
        extra = T.format("combat_forfeit", params)
        # trigger forfeit
        for remove in combat.players:
            combat.clean_combat()
            del combat.monsters_in_play[remove]
            combat.players.remove(remove)
        # kill monsters -> teleport center
        for mon in player.monsters:
            mon.faint()

        return {
            "success": True,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }
