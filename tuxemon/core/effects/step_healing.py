# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.formula import simple_heal

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class StepHealingEffect(CoreEffect):
    """
    Applies the "step_healing" effect to a technique.

    This effect restores HP to one or more target monsters based on the
    number of steps taken by the user's party. The healing scales
    logarithmically, providing diminishing returns as the step count
    increases. This mechanic ties exploration and movement directly into
    combat recovery.

    **Parameters**

    - ``objectives``: Colon-separated string specifying which monsters are
      healed. Examples:
      - ``enemy_monster`` → heals only the enemy.
      - ``own_monster`` → heals only the user.
      - ``enemy_monster:own_monster`` → heals both the enemy and the user.
    - ``healing_factor``: Float multiplier applied to the logarithmic healing
      formula.
    - ``scaling_constant``: Float divisor used in the healing formula to
      normalize step counts.

    **Example**

    .. code-block:: json

        "effects": [
            "step_healing own_monster 1.2 100"
        ]
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
        hit = session.client.combat_session.get_tech_hit(user)

        objectives = self.objectives.split(":")
        tech.hit = tech.accuracy >= hit

        if tech.hit:
            monsters = session.client.combat_session.get_target_monsters(
                objectives, user, target
            )

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
