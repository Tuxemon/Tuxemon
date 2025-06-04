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
class GrabbedEffect(CoreEffect):
    """
    This effect has a chance to apply the grabbed status effect.

    It applies an effect on ranged and reach techniques.

    Parameters:
        divisor: The divisor.
        ranges: Technique range separated by ":".

    """

    name = "grabbed"
    divisor: float
    ranges: str

    def apply_status_target(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        done: bool = False
        ranges = self.ranges.split(":")
        moves = [tech for tech in target.moves if tech.range in ranges]
        if status.phase == "perform_action_status":
            done = True
        # applies effect on techniques
        if done and moves:
            for move in moves:
                move.potency = move.default_potency / self.divisor
                move.power = move.default_power / self.divisor
        return StatusEffectResult(name=status.name, success=done)
