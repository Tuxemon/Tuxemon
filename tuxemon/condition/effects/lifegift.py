# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import fainted
from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.formula import simple_lifeleech

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


@dataclass
class LifeGiftEffect(CondEffect):
    """
    This effect has a chance to apply the lifegift status effect.

    Parameters:
        user: The monster losing HPs.
        target: The monster getting HPs.
        divisor: The number by which target HP is to be divided.

    """

    name = "lifegift"
    divisor: int

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        lifegift: bool = False
        user = condition.link
        assert user
        if condition.phase == "perform_action_status" and not fainted(user):
            damage = simple_lifeleech(user, target, self.divisor)
            user.current_hp = max(0, user.current_hp - damage)
            target.current_hp = min(target.hp, target.current_hp + damage)
            lifegift = True
        if fainted(user):
            target.status.clear()

        return CondEffectResult(
            name=condition.name,
            success=lifegift,
            conditions=[],
            techniques=[],
            extras=[],
        )
