from __future__ import annotations

import random
from typing import NamedTuple, Optional

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class EnragedEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class EnragedEffectParameters(NamedTuple):
    objective: str


class EnragedEffect(TechEffect[EnragedEffectParameters]):
    """
    This effect has a chance to apply the enraged status effect.
    """

    name = "enraged"
    param_class = EnragedEffectParameters

    def apply(self, user: Monster, target: Monster) -> EnragedEffectResult:
        obj = self.parameters.objective
        success = self.move.potency >= random.random()
        if success:
            tech = Technique("status_enraged")
            if obj == "user":
                user.apply_status(tech)
            elif obj == "target":
                target.apply_status(tech)
            return {"status": tech}

        return {"damage": 0, "should_tackle": False, "success": False}
