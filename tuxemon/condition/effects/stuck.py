# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condeffect import CondEffect, CondEffectResult

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class StuckEffectResult(CondEffectResult):
    pass


@dataclass
class StuckEffect(CondEffect):
    """
    This effect has a chance to apply the stuck status effect.

    It applies an effect on melee and touch techniques.

    Parameters:
        divisor: The divisor.
        ranges: Technique range separated by ":".

    """

    name = "stuck"
    divisor: float
    ranges: str

    def apply(
        self, condition: Condition, target: Monster
    ) -> StuckEffectResult:
        done: bool = False
        ranges = self.ranges.split(":")
        moves = [tech for tech in target.moves if tech.range in ranges]
        if condition.phase == "perform_action_status":
            done = True
        # applies effect on techniques
        if done and moves:
            for move in moves:
                move.potency = move.default_potency / self.divisor
                move.power = move.default_power / self.divisor
        return {
            "success": done,
            "condition": None,
            "technique": None,
            "extra": None,
        }
