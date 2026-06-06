# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase
from tuxemon.locale.locale import T
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class NoddingOffEffect(CoreEffect):
    """
    Applies the "noddingoff" status effect.

    This effect simulates a monster falling asleep in battle. Sleep lasts
    for at least one turn, has a chance to end after each turn, and will
    always end after five turns if not resolved earlier.

    **Parameters**

    - ``chance``: Float value representing the probability of remaining asleep
      each turn (e.g., ``0.5`` for 50%).

    **Example**

    .. code-block:: json

        "effects": [
            "noddingoff 0.5"
        ]
    """

    name = "noddingoff"
    chance: float

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        extra: list[str] = []
        tech: list[Technique] = []
        host = status.host

        if status.has_phase(EffectPhase.PRE_CHECKING) and status.on_tech_use:
            skip = Technique.create(status.on_tech_use)
            tech = [skip]

        if status.has_phase(EffectPhase.PERFORM_TECH) and status.nr_turn > 1 and self.wake_up(status):
            params = {"target": host.name.upper()}
            extra = [T.format("combat_state_dozing_end", params)]
            host.status.clear_status(session)
        return StatusEffectResult(
            name=status.name,
            success=True,
            techniques=tech,
            extras=extra,
        )

    def wake_up(self, status: Status) -> bool:
        if random.random() > self.chance:
            return True
        if status.has_exceeded_duration():
            return True
        return False
