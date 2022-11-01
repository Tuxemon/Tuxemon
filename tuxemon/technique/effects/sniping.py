from __future__ import annotations

import random
from typing import NamedTuple, Optional

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class SnipingEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class SnipingEffectParameters(NamedTuple):
    objective: str


class SnipingEffect(TechEffect[SnipingEffectParameters]):
    """
    This effect has a chance to apply the sniping status effect.
    """

    name = "sniping"
    param_class = SnipingEffectParameters

    def apply(self, user: Monster, target: Monster) -> SnipingEffectResult:
        obj = self.parameters.objective
        success = self.move.potency >= random.random()
        if success:
            tech = Technique("status_sniping")
            if obj == "user":
                user.apply_status(tech)
            elif obj == "target":
                target.apply_status(tech)
            return {"status": tech}

        return {"damage": 0, "should_tackle": False, "success": False}
