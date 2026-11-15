# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class FlinchingEffect(CoreEffect):
    """
    Applies the "flinching" status to a monster.

    This effect represents hesitation or recoil, giving the monster a chance
    to miss its next turn. If the monster misses its turn due to flinching,
    the status is cleared.

    **Parameters**

    - ``chance``: The probability of flinching occurring (float between 0 and 1).

    **Example**

    .. code-block:: json

        "effects": [
            "flinching 0.5"
        ]
    """

    name = "flinching"
    chance: float

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        tech: list[Technique] = []
        host = status.host
        if (
            status.has_phase(EffectPhase.PRE_CHECKING)
            and random.random() > self.chance
        ):
            empty = status.on_tech_use
            assert empty
            skip = Technique.create(empty)
            tech = [skip]
            status.advance_round()
            host.status.check_and_clear_use_expiry(session)
        return StatusEffectResult(
            name=status.name, success=True, techniques=tech
        )
