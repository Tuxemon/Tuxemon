# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import get_target_monsters
from tuxemon.formula import simple_damage_calculate
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class StepDamageEffect(TechEffect):
    """
    This effect calculates damage to the target based on the number of steps
    taken by the monster. The damage is scaled using a specified formula, which
    is logarithmic.

    Parameters:
        objectives: The targets for this effect, specified as a string
            (e.g., "enemy_monster" or "enemy_monster:own_monster").
        scaling_factor: A factor used to scale the damage calculation.
        scaling_constant: A constant used in the damage calculation formula.
    """

    name = "step_damage"
    objectives: str
    scaling_factor: float
    scaling_constant: float

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        damage = 0
        monsters: list[Monster] = []
        combat = tech.combat_state
        assert combat

        objectives = self.objectives.split(":")
        tech.hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)

        if tech.hit:
            monsters = get_target_monsters(objectives, tech, user, target)

        if monsters:
            new_power = self.scaling_factor * math.log(
                1 + user.steps / self.scaling_constant
            )
            tech.power = new_power
            damage, _ = simple_damage_calculate(tech, user, target)

            for monster in monsters:
                monster.current_hp = max(0, monster.current_hp - damage)
                # to avoid double registration in the self._damage_map
                if monster != target:
                    combat.enqueue_damage(user, monster, damage)

        return TechEffectResult(
            name=tech.name,
            damage=damage,
            element_multiplier=0.0,
            should_tackle=tech.hit,
            success=tech.hit,
            extras=[],
        )
