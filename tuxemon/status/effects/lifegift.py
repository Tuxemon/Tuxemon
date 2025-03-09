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
class LifeGiftEffect(StatusEffect):
    """
    This effect has a chance to apply the lifegift status effect.

    Parameters:
        user: The monster losing HPs.
        target: The monster getting HPs.
        divisor: The number by which target HP is to be divided.

    """

    name = "lifegift"
    divisor: int

    def apply(self, status: Status, target: Monster) -> StatusEffectResult:
        lifegift: bool = False
        user = status.link
        assert user
        if status.phase == "perform_action_status" and not fainted(user):
            damage = simple_lifeleech(user, target, self.divisor)
            user.current_hp = max(0, user.current_hp - damage)
            target.current_hp = min(target.hp, target.current_hp + damage)
            lifegift = True
        if fainted(user):
            target.status.clear()

        return StatusEffectResult(
            name=status.name,
            success=lifegift,
            statuses=[],
            techniques=[],
            extras=[],
        )
