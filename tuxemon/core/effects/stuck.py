# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
    Applies the "stuck" status effect.

    This effect reduces the effectiveness of certain techniques (e.g.,
    melee or touch-based moves) by lowering their potency and power.
    It simulates a monster being hindered or immobilized, making its
    physical attacks weaker while the status is active.

    **Parameters**

    - ``divisor``: Float value used to reduce potency and power.
      - Must be non-zero.
      - Example: ``2.0`` halves the potency and power of affected moves.
    - ``ranges``: Colon-separated string specifying which technique ranges
      are affected (e.g., ``melee:touch``).

    **Example**

    .. code-block:: json

        "effects": [
            "stuck 2 melee:touch"
        ]
    """

    name = "stuck"
    divisor: float
    ranges: str

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        host = status.host
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
            host.moves.reset_current_stats()

        if done and moves:
            for move in moves:
                move.stats.potency = move.default_stats.potency / self.divisor
                move.stats.power = move.default_stats.power / self.divisor

        return StatusEffectResult(name=status.name, success=done)
