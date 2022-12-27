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


class GrabbedEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


@dataclass
class GrabbedEffect(TechEffect):
    """
    This effect has a chance to apply the grabbed status effect.
    """

    name = "grabbed"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> GrabbedEffectResult:
        obj = self.objective
        success = tech.potency >= random.random()
        if success:
            tech = Technique("status_grabbed")
            if obj == "user":
                user.apply_status(tech)
                formula.simple_grabbed(user)
            elif obj == "target":
                target.apply_status(tech)
                formula.simple_grabbed(target)
            else:
                return
            return {"status": tech}

        return {"damage": 0, "should_tackle": False, "success": False}
