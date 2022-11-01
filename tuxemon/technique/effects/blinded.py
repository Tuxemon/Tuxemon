from __future__ import annotations

import random
from typing import NamedTuple, Optional

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class BlindedEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class BlindedEffectParameters(NamedTuple):
    objective: str


class BlindedEffect(TechEffect[BlindedEffectParameters]):
    """
    This effect has a chance to apply the blinded status effect.
    """

    name = "blinded"
    param_class = BlindedEffectParameters

    def apply(self, user: Monster, target: Monster) -> BlindedEffectResult:
        obj = self.parameters.objective
        success = self.move.potency >= random.random()
        if success:
            tech = Technique("status_blinded")
            if obj == "user":
                user.apply_status(tech)
            elif obj == "target":
                target.apply_status(tech)
            return {"status": tech}

        return {"damage": 0, "should_tackle": False, "success": False}
