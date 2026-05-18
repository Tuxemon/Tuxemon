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
class HealingEffect(CoreEffect):
    """
    Applies the "healing" effect to a technique.

    This effect restores HP to the user or its targets based on the
    technique's healing power. The healing amount is calculated using
    the same formula as the damage that would be dealt by a reliable
    technique of equal power.

    **Example**

    .. code-block:: json

        "effects": [
            "healing"
        ]
    """

    name = "healing"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        targets: list[Monster] = []
        extra: list[str] = []
        done: bool = False

        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit

        if tech.hit:
            targets = session.client.combat_session.get_targets(
                tech, user, target
            )

        if targets:
            for monster in targets:
                heal = formula.simple_heal(tech, monster)
                if monster.hp_ratio < 1.0:
                    heal_amount = min(heal, monster.missing_hp)
                    monster.current_hp += heal_amount
                    done = True
                elif monster.hp_ratio == 1.0:
                    extra = ["combat_full_health"]
        return TechEffectResult(name=tech.name, success=done, extras=extra)
