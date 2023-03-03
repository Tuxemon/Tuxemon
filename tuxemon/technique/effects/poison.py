# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon import formula
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


@dataclass
class PoisonEffect(TechEffect):
    """
    This effect has a chance to apply the poison status effect.
    """

    name = "poison"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        player = self.session.player
        value = float(player.game_variables["random_tech_hit"])
        potency = formula.random.random()
        success = tech.potency >= potency and tech.accuracy >= value
        if success:
            tech = Technique("status_poison")
            if self.objective == "user":
                user.apply_status(tech)
            else:
                target.apply_status(tech)

        damage = formula.simple_poison(target)
        target.current_hp -= damage

        return {
            "damage": damage,
            "should_tackle": bool(damage),
            "success": bool(damage),
            "element_multiplier": 0,
        }
