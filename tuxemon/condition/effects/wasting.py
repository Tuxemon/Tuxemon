# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import fainted
from tuxemon.condition.condeffect import CondEffect, CondEffectResult

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


@dataclass
class WastingEffect(CondEffect):
    """
    Wasting: Take #/16 of your maximum HP in damage each turn
    where # = the number of turns that you have had this condition.

    Parameters:
        divisor: The divisor.

    """

    name = "wasting"
    divisor: int

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        done: bool = False
        if condition.phase == "perform_action_status" and not fainted(target):
            damage = (target.hp // self.divisor) * condition.nr_turn
            target.current_hp = max(0, target.current_hp - damage)
            done = True
        return CondEffectResult(
            name=condition.name,
            success=done,
            conditions=[],
            techniques=[],
            extras=[],
        )
