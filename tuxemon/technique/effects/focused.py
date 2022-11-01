from __future__ import annotations

import random
from typing import NamedTuple, Optional

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class FocusedEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class FocusedEffectParameters(NamedTuple):
    objective: str


class FocusedEffect(TechEffect[FocusedEffectParameters]):
    """
    This effect has a chance to apply the focused status effect.
    """

    name = "focused"
    param_class = FocusedEffectParameters

    def apply(self, user: Monster, target: Monster) -> FocusedEffectResult:
        obj = self.parameters.objective
        success = self.move.potency >= random.random()
        if success:
            tech = Technique("status_focused")
            if obj == "user":
                user.apply_status(tech)
            elif obj == "target":
                target.apply_status(tech)
            return {"status": tech}

        return {"damage": 0, "should_tackle": False, "success": False}
