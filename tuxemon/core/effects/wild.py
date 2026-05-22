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
class WildEffect(CoreEffect):
    """
    Applies the "wild" status to a monster.

    This effect introduces reckless behavior: each turn there is a chance
    that the monster will skip its chosen technique and instead take damage
    equal to a fraction of its maximum HP.

    **Parameters**

    - ``chance``: The probability of getting the penalty (float between 0 and 1).
    - ``divisor``: The divisor used to calculate self-inflicted damage
      (e.g. 8 for one-eighth of max HP).

    **Example**

    .. code-block:: json

        "effects": [
            "wild 0.25 8"
        ]
    """

    name = "wild"
    chance: float
    divisor: int

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        tech: list[Technique] = []
        if (
            status.has_phase(EffectPhase.PRE_CHECKING)
            and random.random() < self.chance
        ):
            user = status.host
            empty = status.on_tech_use
            assert empty
            skip = Technique.create(empty)
            tech = [skip]
            if not user.is_fainted:
                damage = user.hp // self.divisor
                user.current_hp = max(0, user.current_hp - damage)
        return StatusEffectResult(
            name=status.name, success=True, techniques=tech
        )