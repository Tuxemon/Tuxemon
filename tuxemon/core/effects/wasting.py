# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class WastingEffect(CoreEffect):
    """
    Wasting: Take #/16 of your maximum HP in damage each turn
    where # = the number of turns that you have had this status.

    Parameters:
        divisor: The divisor.

    """

    name = "wasting"
    divisor: int

    def apply_status_target(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        done: bool = False
        if status.phase == "perform_action_status" and not target.is_fainted:
            damage = (target.hp // self.divisor) * status.nr_turn
            target.current_hp = max(0, target.current_hp - damage)
            done = True
        return StatusEffectResult(name=status.name, success=done)
