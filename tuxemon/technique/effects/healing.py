# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon.prepare import COEFF_DAMAGE
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
        mon: Monster
        heal: int = 0
        combat = tech.combat_state
        value = combat._random_tech_hit if combat else 0.0
        hit = tech.accuracy >= value
        # define user or target
        if self.objective == "user":
            mon = user
        elif self.objective == "target":
            mon = target
        else:
            raise ValueError(f"{self.objective} must be user or target")
        # check healing power
        if isinstance(tech.healing_power, int):
            heal = (COEFF_DAMAGE + mon.level) * tech.healing_power
        diff = mon.hp - mon.current_hp
        if hit:
            tech.hit = True
            tech.advance_counter_success()
            if diff > 0:
                if heal >= diff:
                    mon.current_hp = mon.hp
                else:
                    mon.current_hp += heal
                done = True
            else:
                extra = "combat_full_health"
        else:
            tech.hit = False
        return {
            "success": done,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }
