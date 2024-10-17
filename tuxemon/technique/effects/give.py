# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condition import Condition
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
        applied = False
        combat = tech.combat_state
        player = user.owner
        assert combat and player

        potency = random.random()
        value = combat._random_tech_hit.get(user, 0.0)
        success = tech.potency >= potency and tech.accuracy >= value

        if success:
            status = Condition()
            status.load(self.condition)
            status.steps = player.steps

            objective_to_monsters = {
                "user": (
                    combat.monsters_in_play_right
                    if user in combat.monsters_in_play_right
                    else combat.monsters_in_play_left
                ),
                "target": (
                    combat.monsters_in_play_left
                    if user in combat.monsters_in_play_right
                    else combat.monsters_in_play_right
                ),
                "both": combat.active_monsters,
            }
            monsters = objective_to_monsters.get(self.objective, [user])

            if player.max_position > 1 and any(
                effect.name == "area" for effect in tech.effects
            ):
                monsters = combat.active_monsters

            for mon in monsters:
                status.link = mon
                mon.apply_status(status)
                applied = True

            if applied:
                combat.reset_status_icons()

        return {
            "success": applied,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": None,
        }
