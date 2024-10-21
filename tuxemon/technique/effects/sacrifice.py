# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class SacrificeEffectResult(TechEffectResult):
    pass


@dataclass
class SacrificeEffect(TechEffect):
    """
    Sacrifice:
    Monster takes damage equal to its current HP,
    and does damage equal to double that amount.

    Parameters:
        multiplier: The percentage of the current HP

    eg user 35/50 HP uses:
        sacrifice 2
    inflicts a damage of 70 HP (enemy)
    inflicts a damage of 35 HP (user) > faints

    """

    name = "sacrifice"
    multiplier: float

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> SacrificeEffectResult:
        tech.hit = tech.accuracy >= (
            tech.combat_state._random_tech_hit.get(user, 0.0)
            if tech.combat_state
            else 0.0
        )
        if tech.hit:
            damage = int(user.current_hp * self.multiplier)
            user.current_hp = 0
            target.current_hp -= damage
        else:
            damage = 0

        return {
            "damage": damage,
            "element_multiplier": 0.0,
            "should_tackle": tech.hit,
            "success": tech.hit,
            "extra": None,
        }
