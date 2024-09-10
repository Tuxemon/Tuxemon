# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class SplashEffectResult(TechEffectResult):
    pass


@dataclass
class SplashEffect(TechEffect):
    """
    Apply splash.

    """

    name = "splash"
    divisor: int

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> SplashEffectResult:
        combat = tech.combat_state
        value = combat._random_tech_hit.get(user, 0.0) if combat else 0.0
        hit = tech.accuracy >= value
        tech.hit = hit
        damage, mult = formula.simple_damage_calculate(tech, user, target)
        if hit:
            target.current_hp -= damage
        else:
            damage //= self.divisor
            target.current_hp -= damage
        return {
            "success": bool(damage),
            "damage": damage,
            "should_tackle": bool(damage),
            "element_multiplier": mult,
            "extra": None,
        }
