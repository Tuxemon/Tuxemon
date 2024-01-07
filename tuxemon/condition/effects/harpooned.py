# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import fainted
from tuxemon.condition.condeffect import CondEffect, CondEffectResult

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class HarpoonedEffectResult(CondEffectResult):
    pass


@dataclass
class HarpoonedEffect(CondEffect):
    """
    Harpooned: If you swap out, take damage equal to 1/8th your maximum HP

    Parameters:
        divisor: The divisor.

    """

    name = "harpooned"
    divisor: int

    def apply(
        self, condition: Condition, target: Monster
    ) -> HarpoonedEffectResult:
        if condition.phase == "add_monster_into_play":
            target.current_hp -= target.hp // self.divisor
            if fainted(target):
                target.faint()
        return {
            "success": True,
            "condition": None,
            "technique": None,
            "extra": None,
        }
