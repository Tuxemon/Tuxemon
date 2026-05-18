# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.formula import simple_damage_calculate

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class StepDamageEffect(CoreEffect):
    """
    Applies the "step_damage" effect to a technique.

    This effect calculates damage to the target based on the number of steps
    taken by the user monster. The damage scales logarithmically, allowing
    diminishing returns as the step count increases. This mechanic ties
    exploration or movement directly into combat effectiveness.

    **Parameters**

    - ``objectives``: Colon-separated string specifying which monsters are
      affected. Examples:
      - ``enemy_monster`` → damages only the enemy.
      - ``own_monster`` → damages only the user.
      - ``enemy_monster:own_monster`` → damages both the enemy and the user.
    - ``scaling_factor``: Float multiplier applied to the logarithmic damage
      formula.
    - ``scaling_constant``: Float divisor used in the logarithmic formula to
      normalize step counts.

    **Example**

    .. code-block:: json

        "effects": [
            "step_damage enemy_monster 1.5 100"
        ]
    """

    name = "step_damage"
    objectives: str
    scaling_factor: float
    scaling_constant: float

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        damage = 0
        monsters: list[Monster] = []

        objectives = self.objectives.split(":")
        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit

        if tech.hit:
            monsters = session.client.combat_session.get_target_monsters(
                objectives, user, target
            )

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
                    session.client.combat_session.enqueue_damage(
                        user, monster, damage
                    )

        return TechEffectResult(
            name=tech.name,
            damage=damage,
            should_tackle=tech.hit,
            success=tech.hit,
        )
