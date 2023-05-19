# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class SplashEffectResult(TechEffectResult):
    damage: int
    element_multiplier: float
    should_tackle: bool


@dataclass
class SplashEffect(TechEffect):
    """
    Apply splash.

    """

    name = "splash"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> SplashEffectResult:
        player = self.session.player
        value = float(player.game_variables["random_tech_hit"])
        hit = tech.accuracy >= value
        damage, mult = formula.simple_damage_calculate(tech, user, target)
        tech.advance_counter_success()
        if hit:
            tech.hit = True
            target.current_hp -= damage
        else:
            tech.hit = True
            damage //= 2
            target.current_hp -= damage
        return {
            "success": bool(damage),
            "damage": damage,
            "should_tackle": bool(damage),
            "element_multiplier": mult,
        }
