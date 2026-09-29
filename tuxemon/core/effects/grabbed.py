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
class GrabbedEffect(CoreEffect):
    """
    Applies the "grabbed" status to a monster.

    This effect reduces the potency and power of the monster's ranged or
    reach techniques by dividing their default values with the specified
    divisor. It represents being physically restrained, limiting the
    effectiveness of certain moves.

    **Parameters**

    - ``divisor``: The divisor used to reduce potency and power (must be non-zero).
    - ``ranges``: Colon-separated list of technique ranges affected
      (e.g. ``ranged:reach``).

    **Example**

    .. code-block:: json

        "effects": [
            "grabbed 2 ranged:reach"
        ]
    """

    name = "grabbed"
    divisor: float
    ranges: str

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        if self.divisor == 0:
            raise ValueError("StuckEffect divisor must be non-zero.")

        done: bool = False
        host = status.host
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
