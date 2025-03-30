# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class SplashEffect(TechEffect):
    """
    Apply splash.

    """

    name = "splash"
    divisor: int

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        combat = tech.combat_state
        assert combat
        tech.hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)

        damage, mult = formula.simple_damage_calculate(tech, user, target)
        targets = combat.get_targets(tech, user, target)

        if not tech.hit:
            damage //= self.divisor

        if targets:
            for monster in targets:
                monster.current_hp = max(0, monster.current_hp - damage)
                # to avoid double registration in the self._damage_map
                if monster != target:
                    combat.enqueue_damage(user, monster, damage)

        return TechEffectResult(
            name=tech.name,
            success=bool(damage),
            damage=damage,
            should_tackle=bool(damage),
            element_multiplier=mult,
            extras=[],
        )
