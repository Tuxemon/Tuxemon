# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condeffect import CondEffect, CondEffectResult

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class PoisonedEffectResult(CondEffectResult):
    pass


@dataclass
class PoisonedEffect(CondEffect):
    """
    This effect has a chance to apply the poisoned status.

    Parameters:
        divisor: The divisor.

    """

    name = "poisoned"
    divisor: int

    def apply(
        self, condition: Condition, target: Monster
    ) -> PoisonedEffectResult:
        poisoned: bool = False
        if condition.phase == "perform_action_status":
            target.current_hp -= target.hp // self.divisor
            poisoned = True

        return {
            "success": poisoned,
            "condition": None,
            "technique": None,
            "extra": None,
        }
