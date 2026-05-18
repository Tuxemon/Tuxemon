# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class RampEffect(CoreEffect):
    """
    Gradually increases a technique's power each consecutive turn it is used,
    allowing certain moves to grow stronger over time. This effect is commonly
    used for techniques such as ``Rollout``, ``Ice Ball``, or ``Fury Cutter``,
    where repeated use amplifies damage output.

    **Parameters**

    - ``multiplier``: The factor applied to the technique's power for each
      additional consecutive use. A value of ``2.0`` doubles the power each turn,
      while other values adjust the growth rate accordingly.

    **Example**

    .. code-block:: json

        "effects": [
            "ramp 2.0"
        ]
    """

    name = "ramp"
    multiplier: float = 2.0

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        user.ramp_counter += 1
        tech.power = int(
            tech.power * (self.multiplier ** (user.ramp_counter - 1))
        )
        return TechEffectResult(name=tech.name, success=True)
