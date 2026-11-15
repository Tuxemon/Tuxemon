# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.locale.locale import T

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class MultiAttackEffect(CoreEffect):
    """
    Applies the "multiattack" effect to a technique.

    This effect allows a technique to be executed multiple times in the
    same turn, up to the specified number of repetitions. Each successful
    hit enqueues another attack action until the maximum count is reached.

    **Parameters**

    - ``times``: Integer value indicating how many times the technique
      can be repeated in a single turn.

    **Example**

    .. code-block:: json

        "effects": [
            "multiattack 3"
        ]
    """

    name = "multiattack"
    times: int

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        combat = session.client.combat_session

        hit_count = 0
        total_damage = 0
        extras: list[str] = []

        for _ in range(self.times):
            combat.set_tech_hit(user)
            hit_roll = combat.get_tech_hit(user)
            hit = tech.accuracy >= hit_roll

            if not hit:
                break

            hit_count += 1
            dmg, _ = formula.simple_damage_calculate(tech, user, target)
            total_damage += dmg

        success = hit_count > 0

        if success:
            target.current_hp = max(0, target.current_hp - total_damage)
            params = {"hit_count": hit_count}
            extract_text = T.format("combat_multiattack", params)
            extras = [extract_text]

        return TechEffectResult(
            name=tech.name,
            success=success,
            should_tackle=success,
            damage=total_damage,
            extras=extras,
            hit_count=hit_count,
        )
