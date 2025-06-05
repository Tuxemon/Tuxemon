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
class HarpoonedEffect(CoreEffect):
    """
    Harpooned: If you swap out, take damage equal to 1/8th your maximum HP

    Parameters:
        divisor: The divisor.

    """

    name = "harpooned"
    divisor: int

    def apply_status_target(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        if status.phase == "add_monster_into_play":
            damage = target.hp // self.divisor
            target.current_hp = max(0, target.current_hp - damage)
            if target.is_fainted:
                target.faint()
        return StatusEffectResult(name=status.name, success=True)
