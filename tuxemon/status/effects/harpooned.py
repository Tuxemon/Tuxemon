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
class HarpoonedEffect(StatusEffect):
    """
    Harpooned: If you swap out, take damage equal to 1/8th your maximum HP

    Parameters:
        divisor: The divisor.

    """

    name = "harpooned"
    divisor: int

    def apply(self, status: Status, target: Monster) -> StatusEffectResult:
        if status.phase == "add_monster_into_play":
            damage = target.hp // self.divisor
            target.current_hp = max(0, target.current_hp - damage)
            if fainted(target):
                target.faint()
        return StatusEffectResult(
            name=status.name,
            success=True,
            statuses=[],
            techniques=[],
            extras=[],
        )
