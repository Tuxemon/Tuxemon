from __future__ import annotations

import random
from typing import NamedTuple, Optional

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class ExhaustedEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class ExhaustedEffectParameters(NamedTuple):
    objective: str


class ExhaustedEffect(TechEffect[ExhaustedEffectParameters]):
    """
    This effect has a chance to apply the exhausted status effect.
    """

    name = "exhausted"
    param_class = ExhaustedEffectParameters

    def apply(self, user: Monster, target: Monster) -> ExhaustedEffectResult:
        obj = self.parameters.objective
        success = self.move.potency >= random.random()
        if success:
            tech = Technique("status_exhausted")
            if obj == "user":
                user.apply_status(tech)
            elif obj == "target":
                target.apply_status(tech)
            return {"status": tech}

        return {"damage": 0, "should_tackle": False, "success": False}
