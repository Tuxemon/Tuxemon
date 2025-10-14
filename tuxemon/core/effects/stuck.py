# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class StuckEffect(CoreEffect):
    """
    This effect has a chance to apply the stuck status effect.

    It applies an effect on melee and touch techniques.

    Parameters:
        divisor: The divisor.
        ranges: Technique range separated by ":".
    """

    name = "stuck"
    divisor: float
    ranges: str

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        host = status.get_host()
        if self.divisor == 0:
            raise ValueError("StuckEffect divisor must be non-zero.")

        done: bool = False
        ranges = self.ranges.split(":")
        moves = [
            tech for tech in host.moves.get_moves() if tech.range in ranges
        ]

        if status.has_phase(EffectPhase.PERFORM_STATUS):
            done = True
        elif status.has_phase(EffectPhase.ON_END):
            host.moves.set_stats()

        if done and moves:
            for move in moves:
                move.potency = move.default_potency / self.divisor
                move.power = move.default_power / self.divisor
        return StatusEffectResult(name=status.name, success=done)
