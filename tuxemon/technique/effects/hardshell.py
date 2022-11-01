from __future__ import annotations

import random
from typing import NamedTuple, Optional

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class HardShellEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class HardShellEffectParameters(NamedTuple):
    objective: str


class HardShellEffect(TechEffect[HardShellEffectParameters]):
    """
    This effect has a chance to apply the hard shell status effect.
    """

    name = "hardshell"
    param_class = HardShellEffectParameters

    def apply(self, user: Monster, target: Monster) -> HardShellEffectResult:
        obj = self.parameters.objective
        success = self.move.potency >= random.random()
        if success:
            tech = Technique("status_hardshell")
            if obj == "user":
                user.apply_status(tech)
            elif obj == "target":
                target.apply_status(tech)
            return {"status": tech}

        return {"damage": 0, "should_tackle": False, "success": False}
