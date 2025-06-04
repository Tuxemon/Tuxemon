# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import get_target_monsters
from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.formula import simple_heal

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class StepHealingEffect(CoreEffect):
    """
    This effect calculates healing to the target based on the combined
    step count of the party. The healing is scaled using a specified
    formula, which is logarithmic.

    Parameters:
        objectives: The targets for this effect, specified as a string
            (e.g., "enemy_monster" or "enemy_monster:own_monster").
        healing_factor: A factor used to scale the healing calculation.
        scaling_constant: A constant used in the healing calculation formula.
    """

    name = "step_healing"
    objectives: str
    healing_factor: float
    scaling_constant: float

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        monsters: list[Monster] = []
        extra: list[str] = []
        done: bool = False
        combat = tech.combat_state
        assert combat

        objectives = self.objectives.split(":")
        tech.hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)

        if tech.hit:
            monsters = get_target_monsters(objectives, tech, user, target)

        if monsters:
            for monster in monsters:
                new_power = self.healing_factor * math.log(
                    1 + user.steps / self.scaling_constant
                )
                tech.healing_power = new_power
                heal = simple_heal(tech, monster)
                if monster.hp_ratio < 1.0:
                    heal_amount = min(heal, monster.missing_hp)
                    monster.current_hp += heal_amount
                    done = True
                elif monster.hp_ratio == 1.0:
                    extra = ["combat_full_health"]
        return TechEffectResult(name=tech.name, success=done, extras=extra)
