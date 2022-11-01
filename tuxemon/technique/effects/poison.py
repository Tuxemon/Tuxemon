from __future__ import annotations

import random
from typing import NamedTuple, Optional

from tuxemon import formula
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class PoisonEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class PoisonEffectParameters(NamedTuple):
    pass


class PoisonEffect(TechEffect[PoisonEffectParameters]):
    """
    This effect has a chance to apply the poison status effect.
    """

    name = "poison"
    param_class = PoisonEffectParameters

    def apply(self, user: Monster, target: Monster) -> PoisonEffectResult:
        success = self.move.potency >= random.random()
        if success:
            tech = Technique("status_poison")
            target.apply_status(tech)
            # exception: applies status to the user
            if self.move.slug == "fester":
                user.apply_status(tech)
            return {"status": tech}

        damage = formula.simple_poison(self.move, target)
        target.current_hp -= damage

        return {
            "damage": damage,
            "should_tackle": bool(damage),
            "success": bool(damage),
        }
