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
class WastingEffect(CoreEffect):
    """
    Applies the "wasting" status effect.

    This effect causes a monster to lose a fraction of its maximum HP each
    round, with the damage increasing over time. The damage scales with the
    number of rounds the status has performed, counted by the effect itself
    on the status's round counter (``advance_round`` / ``nr_round``).

    The round is counted at the start of every ``PERFORM_STATUS`` phase,
    before deciding whether to deal damage, so rounds in which no damage is
    dealt still count toward the ramp. The turn counter (``nr_turn``) is
    not used: it only runs for statuses with a duration, and it is already
    on turn 2 by the first time the status performs, which would open the
    ramp at a double dose.

    **Parameters**

      - ``divisor``: Integer divisor used to calculate base damage.
      - Example: With ``divisor = 16``, the monster takes
        ``(max_hp / 16) * n`` damage in the n-th round: one dose in the
        first, two in the second and so on, so a monster at full HP
        faints in the sixth round. Re-applying the status (stacking)
        restarts the ramp.

    **Example**

    .. code-block:: json

        "effects": [
            "wasting 16"
        ]
    """

    name = "wasting"
    divisor: int

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        done: bool = False
        host = status.host
        if status.has_phase(EffectPhase.PERFORM_STATUS):
            # count the round before anything can skip the damage, so the
            # ramp keeps climbing through rounds that deal none
            status.advance_round()
            if not host.is_fainted:
                damage = (host.hp // self.divisor) * status.nr_round
                host.current_hp = max(0, host.current_hp - damage)
                done = True
        return StatusEffectResult(name=status.name, success=done)
