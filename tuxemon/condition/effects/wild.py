# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon.combat import fainted
from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class WildEffectResult(CondEffectResult):
    pass


@dataclass
class WildEffect(CondEffect):
    """
    Wild: 1/4 chance each turn that instead of using the chosen
    technique, you take 1/8 your maximum HP in unmodified damage.

    Parameters:
        chance: The chance.
        divisor: The divisor.

    """

    name = "wild"
    chance: float
    divisor: int

    def apply(self, condition: Condition, target: Monster) -> WildEffectResult:
        skip: Optional[Technique] = None
        if condition.phase == "pre_checking" and random.random() > self.chance:
            user = condition.link
            empty = condition.repl_tech
            assert user and empty
            skip = Technique()
            skip.load(empty)
            if not fainted(user):
                user.current_hp -= user.hp // self.divisor
        return {
            "success": True,
            "condition": None,
            "technique": skip,
            "extra": None,
        }
