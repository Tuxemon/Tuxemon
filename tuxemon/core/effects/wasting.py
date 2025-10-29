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
class WastingEffect(CoreEffect):
    """
    Wasting: Take #/16 of your maximum HP in damage each turn
    where # = the number of turns that you have had this status.

    Parameters:
        divisor: The divisor.
    """

    name = "wasting"
    divisor: int

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        done: bool = False
        host = status.host
        if (
            status.has_phase(EffectPhase.PERFORM_STATUS)
            and not host.is_fainted
        ):
            damage = (host.hp // self.divisor) * status.nr_turn
            host.current_hp = max(0, host.current_hp - damage)
            done = True
        return StatusEffectResult(name=status.name, success=done)
