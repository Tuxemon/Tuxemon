# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class DamageEffect(CoreEffect):
    """
    Apply damage.

    This effect applies damage to a target monster or multiple monsters.
    This effect will only be applied if "damage" is defined in the relevant
    technique's effect list.
    """

    name = "damage"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        damage = 0
        mult = 1.0
        targets: list[Monster] = []

        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit

        if tech.hit and not target.out_of_range:
            damage, mult = formula.simple_damage_calculate(tech, user, target)
            targets = session.client.combat_session.get_targets(
                tech, user, target
            )

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
            damage=damage,
            element_multiplier=mult,
            should_tackle=bool(damage),
            success=bool(damage),
        )
