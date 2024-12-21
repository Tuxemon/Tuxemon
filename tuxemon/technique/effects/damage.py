# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class DamageEffectResult(TechEffectResult):
    pass


@dataclass
class DamageEffect(TechEffect):
    """
    Apply damage.

    This effect applies damage to a target monster or multiple monsters.
    This effect will only be applied if "damage" is defined in the relevant
    technique's effect list.
    """

    name = "damage"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> DamageEffectResult:
        damage = 0
        mult = 1.0
        targets: list[Monster] = []

        combat = tech.combat_state
        assert combat
        tech.hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)

        if tech.hit and not target.out_of_range:
            damage, mult = formula.simple_damage_calculate(tech, user, target)
            targets = combat.get_targets(tech, user, target)

        if targets:
            for monster in targets:
                monster.current_hp = max(0, monster.current_hp - damage)
                # to avoid double registration in the self._damage_map
                if monster != target:
                    combat.enqueue_damage(user, monster, damage)

        return {
            "damage": damage,
            "element_multiplier": mult,
            "should_tackle": bool(damage),
            "success": bool(damage),
            "extra": None,
        }
