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
class SpikyEffect(CoreEffect):
    """
    Applies the "spiky" status effect.

    This effect damages an incoming monster when it is swapped into battle.
    The damage is calculated as a fraction of the monster's maximum HP,
    determined by the specified divisor.

    **Parameters**

    - ``divisor``: Integer value used to calculate the damage.
      - Damage is calculated as ``host.hp // divisor``.
      - Example: With a divisor of 8, the monster takes 1/8th of its maximum HP.

    **Example**

    .. code-block:: json

        "effects": [
            "spiky 8"
        ]
    """

    name = "spiky"
    divisor: int

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        host = status.host
        if status.has_phase(EffectPhase.SWAP_MONSTER):
            damage = host.hp // self.divisor
            host.current_hp = max(0, host.current_hp - damage)
            if host.is_fainted:
                host.current_hp = 0
        return StatusEffectResult(name=status.name, success=True)
