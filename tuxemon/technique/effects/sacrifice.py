# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class SacrificeEffect(TechEffect):
    """
    Sacrifice:
    Monster takes damage equal to its current (or part) HP,

    Parameters:
        multiplier: The percentage of the current HP

    eg user 35/50 HP uses:
        sacrifice 1
    inflicts a damage of 35 HP (enemy)
    inflicts a damage of 35 HP (user) > faints

    """

    name = "sacrifice"
    multiplier: float

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if not 0 <= self.multiplier <= 1:
            raise ValueError("Multiplier must be a float between 0 and 1")

        combat = tech.combat_state
        assert combat
        tech.hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)

        if tech.hit:
            damage = int(user.current_hp * self.multiplier)
            user.current_hp = 0
            target.current_hp = max(0, target.current_hp - damage)
        else:
            damage = 0

        return TechEffectResult(
            name=tech.name,
            damage=damage,
            element_multiplier=0.0,
            should_tackle=tech.hit,
            success=tech.hit,
            extras=[],
        )
