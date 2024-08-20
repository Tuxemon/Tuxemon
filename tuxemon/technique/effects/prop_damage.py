# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class PropDamageEffectResult(TechEffectResult):
    pass


@dataclass
class PropDamageEffect(TechEffect):
    """
    Proportional Damage:
    This effect does damage to the enemy equal
    to % of the target's / user's maximum HP.

    Parameters:
        objective: User HP or target HP.
        proportional: The percentage of the max HP

    eg prop_damage target,4 (1/4 max enemy HP)

    """

    name = "prop_damage"
    objective: str
    proportional: int

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> PropDamageEffectResult:
        combat = tech.combat_state
        value = combat._random_tech_hit.get(user, 0.0) if combat else 0.0
        hit = tech.accuracy >= value
        tech.hit = hit
        if hit:
            tech.advance_counter_success()
            reference_hp = target.hp if self.objective == "target" else user.hp
            target.current_hp -= reference_hp // self.proportional
        else:
            damage = 0

        return {
            "damage": damage,
            "element_multiplier": 0.0,
            "should_tackle": bool(damage),
            "success": bool(damage),
            "extra": None,
        }
