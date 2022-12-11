from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from tuxemon import formula
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class StuckEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


@dataclass
class StuckEffect(TechEffect):
    """
    This effect has a chance to apply the stuck status effect.
    """

    name = "stuck"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> StuckEffectResult:
        obj = self.objective
        success = tech.potency >= random.random()
        if success:
            tech = Technique("status_stuck")
            if obj == "user":
                user.apply_status(tech)
                formula.simple_stuck(user)
            elif obj == "target":
                target.apply_status(tech)
                formula.simple_stuck(target)
            else:
                return
            return {"status": tech}

        return {"damage": 0, "should_tackle": False, "success": False}
