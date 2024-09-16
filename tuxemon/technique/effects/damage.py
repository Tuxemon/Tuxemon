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

    This effect applies damage to a target monster. This effect will only
    be applied if "damage" is defined in the relevant technique's effect
    list.

    Parameters:
        user: The Monster object that used this technique.
        target: The Monster object that we are using this technique on.

    Returns:
        Dict summarizing the result.

    """

    name = "damage"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> DamageEffectResult:
        combat = tech.combat_state
        value = combat._random_tech_hit.get(user, 0.0) if combat else 0.0
        hit = tech.accuracy >= value
        tech.hit = hit
        if hit and not target.out_of_range:
            damage, mult = formula.simple_damage_calculate(tech, user, target)
            target.current_hp -= damage
        else:
            damage = 0
            mult = 1.0

        return {
            "damage": damage,
            "element_multiplier": mult,
            "should_tackle": bool(damage),
            "success": bool(damage),
            "extra": None,
        }
