# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class PropHealingEffectResult(TechEffectResult):
    pass


@dataclass
class PropHealingEffect(TechEffect):
    """
    Proportional Healing:
    This effect does healing to the user equal
    to % of the target's / user's maximum HP.

    Parameters:
        objective: User HP or target HP.
        proportional: The percentage of the max HP

    eg prop_healing target,0.25 (1/4 max enemy HP)

    """

    name = "prop_healing"
    objective: str
    proportional: float

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> PropHealingEffectResult:
        tech.hit = tech.accuracy >= (
            tech.combat_state._random_tech_hit.get(user, 0.0)
            if tech.combat_state
            else 0.0
        )
        if tech.hit:
            reference_hp = target.hp if self.objective == "target" else user.hp
            amount = (reference_hp) * self.proportional
            user.current_hp = min(user.hp, user.current_hp + int(amount))

        return {
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "success": tech.hit,
            "extra": None,
        }
