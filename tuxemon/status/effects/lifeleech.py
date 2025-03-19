# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import fainted
from tuxemon.formula import simple_lifeleech
from tuxemon.status.statuseffect import StatusEffect, StatusEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.status.status import Status


@dataclass
class LifeLeechEffect(StatusEffect):
    """
    This effect has a chance to apply the lifeleech status effect.

    Parameters:
        user: The monster getting HPs.
        target: The monster losing HPs.
        divisor: The number by which target HP is to be divided.

    """

    name = "lifeleech"
    divisor: int

    def apply(self, status: Status, target: Monster) -> StatusEffectResult:
        lifeleech: bool = False
        user = status.link
        assert user
        if status.phase == "perform_action_status" and not fainted(user):
            damage = simple_lifeleech(user, target, self.divisor)
            target.current_hp = max(0, target.current_hp - damage)
            user.current_hp = min(user.hp, user.current_hp + damage)
            lifeleech = True
        if fainted(user):
            target.status.clear()

        return StatusEffectResult(
            name=status.name,
            success=lifeleech,
            statuses=[],
            techniques=[],
            extras=[],
        )
