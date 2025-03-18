# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.formula import weakest_link
from tuxemon.locale import T
from tuxemon.status.statuseffect import StatusEffect, StatusEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.status.status import Status


@dataclass
class PoisonedEffect(StatusEffect):
    """
    This effect has a chance to apply the poisoned status.

    Parameters:
        divisor: The divisor.

    """

    name = "poisoned"
    divisor: int

    def apply(self, status: Status, target: Monster) -> StatusEffectResult:
        poisoned: bool = False
        params = {"target": target.name, "method": status.name}
        if status.phase == "perform_action_status":
            damage = target.hp / self.divisor
            mult = weakest_link(status.modifiers, target)
            damage *= mult
            if damage > 0:
                poisoned = True
                target.current_hp = max(0, target.current_hp - int(damage))
            else:
                status.use_failure = T.format("combat_state_immune", params)
                target.status = []

        return StatusEffectResult(
            name=status.name,
            success=poisoned,
            statuses=[],
            techniques=[],
            extras=[],
        )
