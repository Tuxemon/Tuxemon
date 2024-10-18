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
class BurntEffect(CondEffect):
    """
    This effect has a chance to apply the burnt status.

    Parameters:
        divisor: The divisor.

    """

    name = "burnt"
    divisor: int

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        burnt: bool = False
        if condition.phase == "perform_action_status":
            target.current_hp -= target.hp // self.divisor
            burnt = True

        return CondEffectResult(
            name=condition.name,
            success=burnt,
            condition=[],
            technique=[],
            extra=[],
        )
