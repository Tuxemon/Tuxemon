from __future__ import annotations

import random
from typing import NamedTuple, Optional

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class ChargedUpEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class ChargedUpEffectParameters(NamedTuple):
    objective: str


class ChargedUpEffect(TechEffect[ChargedUpEffectParameters]):
    """
    This effect has a chance to apply the charged up status effect.
    """

    name = "chargedup"
    param_class = ChargedUpEffectParameters

    def apply(self, user: Monster, target: Monster) -> ChargedUpEffectResult:
        obj = self.parameters.objective
        success = self.move.potency >= random.random()
        if success:
            tech = Technique("status_chargedup")
            if obj == "user":
                user.apply_status(tech)
            elif obj == "target":
                target.apply_status(tech)
            return {"status": tech}

        return {"damage": 0, "should_tackle": False, "success": False}
