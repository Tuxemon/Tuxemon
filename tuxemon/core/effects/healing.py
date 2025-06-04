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
class HealingEffect(CoreEffect):
    """
    Healing is based on healing power.

    Healing power indicates that the technique heals its user an
    amount equal to the damage done by a reliable technique of
    the same power.
    """

    name = "healing"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        targets: list[Monster] = []
        extra: list[str] = []
        done: bool = False

        combat = tech.combat_state
        assert combat
        tech.hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)

        if tech.hit:
            targets = combat.get_targets(tech, user, target)

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
