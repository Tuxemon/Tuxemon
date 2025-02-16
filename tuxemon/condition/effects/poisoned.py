# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.formula import condition_weakest_link

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


@dataclass
class PoisonedEffect(CondEffect):
    """
    This effect has a chance to apply the poisoned status.

    Parameters:
        divisor: The divisor.

    """

    name = "poisoned"
    divisor: int

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        poisoned: bool = False
        if condition.phase == "perform_action_status":
            damage = target.hp / self.divisor
            mult = condition_weakest_link(condition.damage_modifiers, target)
            damage *= mult
            target.current_hp = max(0, target.current_hp - int(damage))
            poisoned = True

        return CondEffectResult(
            name=condition.name,
            success=poisoned,
            conditions=[],
            techniques=[],
            extras=[],
        )
