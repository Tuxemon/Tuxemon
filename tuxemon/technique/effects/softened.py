from __future__ import annotations

import random
from typing import NamedTuple, Optional

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class SoftenedEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class SoftenedEffectParameters(NamedTuple):
    objective: str


class SoftenedEffect(TechEffect[SoftenedEffectParameters]):
    """
    This effect has a chance to apply the softened status effect.
    """

    name = "softened"
    param_class = SoftenedEffectParameters

    def apply(self, user: Monster, target: Monster) -> SoftenedEffectResult:
        obj = self.parameters.objective
        success = self.move.potency >= random.random()
        if success:
            tech = Technique("status_softened")
            if obj == "user":
                user.apply_status(tech)
            elif obj == "target":
                target.apply_status(tech)
            return {"status": tech}

        return {"damage": 0, "should_tackle": False, "success": False}
