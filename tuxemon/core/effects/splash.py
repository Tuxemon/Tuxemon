# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class SplashEffect(CoreEffect):
    """
    Applies the "splash" effect to a technique.

    This effect distributes damage across multiple targets. If the technique
    misses, the damage is reduced by dividing it with the specified divisor.
    Otherwise, full damage is applied to all valid targets.

    **Parameters**

    - ``divisor``: Integer value used to reduce damage when the technique
      misses. Damage is divided by this value.

    **Example**

    .. code-block:: json

        "effects": [
            "splash 2"
        ]
    """

    name = "splash"
    divisor: int

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit

        damage, mult = formula.simple_damage_calculate(tech, user, target)
        targets = session.client.combat_session.get_targets(tech, user, target)

        if not tech.hit:
            damage //= self.divisor

        if targets:
            for monster in targets:
                monster.current_hp = max(0, monster.current_hp - damage)
                # to avoid double registration in the self._damage_map
                if monster != target:
                    session.client.combat_session.enqueue_damage(
                        user, monster, damage
                    )

        return TechEffectResult(
            name=tech.name,
            success=bool(damage),
            damage=damage,
            should_tackle=bool(damage),
            element_multiplier=mult,
        )
