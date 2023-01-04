# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from tuxemon import formula
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class PoisonEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


@dataclass
class PoisonEffect(TechEffect):
    """
    This effect has a chance to apply the poison status effect.
    """

    name = "poison"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> PoisonEffectResult:
        success = tech.potency >= random.random()
        if success:
            tech = Technique("status_poison")
            if self.objective == "user":
                user.apply_status(tech)
            elif self.objective == "target":
                target.apply_status(tech)
            return {"status": tech}

        damage = formula.simple_poison(target)
        target.current_hp -= damage

        return {
            "damage": damage,
            "should_tackle": bool(damage),
            "success": bool(damage),
        }
