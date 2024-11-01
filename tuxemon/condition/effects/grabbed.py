# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condeffect import CondEffect, CondEffectResult

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


@dataclass
class GrabbedEffect(CondEffect):
    """
    This effect has a chance to apply the grabbed status effect.

    It applies an effect on ranged and reach techniques.

    Parameters:
        divisor: The divisor.
        ranges: Technique range separated by ":".

    """

    name = "grabbed"
    divisor: float
    ranges: str

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
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
        return CondEffectResult(
            name=condition.name,
            success=done,
            conditions=[],
            techniques=[],
            extras=[],
        )
