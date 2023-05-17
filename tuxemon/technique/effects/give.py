# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster


class GiveEffectResult(TechEffectResult):
    pass


@dataclass
class GiveEffect(TechEffect):
    """
    This effect has a chance to give a status effect.
    """

    name = "give"
    condition: str
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> GiveEffectResult:
        player = self.session.player
        potency = random.random()
        value = float(player.game_variables["random_tech_hit"])
        success = tech.potency >= potency and tech.accuracy >= value
        if success:
            status = Technique()
            status.load(self.condition)
            # 2 vs 2, give status both monsters
            if player.max_position > 1:
                monsters: Sequence[Monster] = []
                assert tech.combat_state
                combat = tech.combat_state
                human = combat.monsters_in_play_human
                opponent = combat.monsters_in_play_ai
                if player.isplayer:
                    if self.objective == "user":
                        monsters = human
                        for m in monsters:
                            status.link = m
                    elif self.objective == "target":
                        monsters = opponent
                else:
                    if self.objective == "user":
                        monsters = opponent
                        for m in monsters:
                            status.link = m
                    elif self.objective == "target":
                        monsters = human
                for mon in monsters:
                    mon.apply_status(status)
                return {"success": True}
            else:
                status.link = user
                if self.objective == "user":
                    user.apply_status(status)
                elif self.objective == "target":
                    target.apply_status(status)
                return {"success": True}

        return {"success": False}
