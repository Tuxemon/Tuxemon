# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon import formula
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class HealingEffectResult(TechEffectResult):
    pass


@dataclass
class HealingEffect(TechEffect):
    """
    Healing is based on healing power.

    Healing power indicates that the technique heals its user an
    amount equal to the damage done by a reliable technique of
    the same power.

    """

    name = "healing"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> HealingEffectResult:
        extra: Optional[str] = None
        done: bool = False

        tech.hit = tech.accuracy >= (
            tech.combat_state._random_tech_hit.get(user, 0.0)
            if tech.combat_state
            else 0.0
        )

        mon = user if self.objective == "user" else target

        if tech.hit:
            heal = formula.simple_heal(tech, mon)
            if mon.current_hp < mon.hp:
                heal_amount = min(heal, mon.hp - mon.current_hp)
                mon.current_hp += heal_amount
                done = True
            elif mon.current_hp == mon.hp:
                extra = "combat_full_health"
        return {
            "success": done,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }
