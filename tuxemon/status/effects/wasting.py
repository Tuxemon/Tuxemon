# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import fainted
from tuxemon.status.statuseffect import StatusEffect, StatusEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.status.status import Status


@dataclass
class WastingEffect(StatusEffect):
    """
    Wasting: Take #/16 of your maximum HP in damage each turn
    where # = the number of turns that you have had this status.

    Parameters:
        divisor: The divisor.

    """

    name = "wasting"
    divisor: int

    def apply(self, status: Status, target: Monster) -> StatusEffectResult:
        done: bool = False
        if status.phase == "perform_action_status" and not fainted(target):
            damage = (target.hp // self.divisor) * status.nr_turn
            target.current_hp = max(0, target.current_hp - damage)
            done = True
        return StatusEffectResult(
            name=status.name,
            success=done,
            statuses=[],
            techniques=[],
            extras=[],
        )
