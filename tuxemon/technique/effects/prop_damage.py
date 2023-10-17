# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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

    eg prop_damage target,0.25 (1/4 max enemy HP)

    """

    name = "prop_damage"
    objective: str
    proportional: float

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> PropDamageEffectResult:
        player = self.session.player
        value = float(player.game_variables["random_tech_hit"])
        mult = 1.0
        hit = tech.accuracy >= value
        if hit:
            damage = None
            tech.hit = True
            tech.advance_counter_success()
            if self.objective == "target":
                damage = target.hp * self.proportional
            else:
                damage = user.hp * self.proportional
            target.current_hp -= int(damage)
        else:
            tech.hit = False
            damage = 0

        return {
            "damage": int(damage),
            "element_multiplier": mult,
            "should_tackle": bool(damage),
            "success": bool(damage),
            "extra": None,
        }
