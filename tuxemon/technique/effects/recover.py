from __future__ import annotations

import random
from typing import NamedTuple, Optional

from tuxemon import formula
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class RecoverEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class RecoverEffectParameters(NamedTuple):
    pass


class RecoverEffect(TechEffect[RecoverEffectParameters]):
    """
    This effect has a chance to apply the recovering status effect.
    """

    name = "recover"
    param_class = RecoverEffectParameters

    def apply(self, user: Monster, target: Monster) -> RecoverEffectResult:
        success = self.move.potency >= random.random()
        if success:
            tech = Technique("status_recover", link=user)
            user.apply_status(tech)
            return {"status": tech}

        # avoids Nonetype situation and reset the user
        if self.user is None:
            heal = formula.simple_recover(self.move, user)
            user.current_hp += heal
        else:
            heal = formula.simple_recover(self.move, self.user)
            self.user.current_hp += heal

        return {
            "damage": heal,
            "should_tackle": False,
            "success": bool(heal),
        }
