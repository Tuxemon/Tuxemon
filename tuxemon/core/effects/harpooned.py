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
class HarpoonedEffect(CoreEffect):
    """
    Applies the "harpooned" status to a monster.

    This effect causes the affected monster to take damage when it is swapped
    out of battle. The damage is calculated as the monster's maximum HP divided
    by the specified divisor. If the monster faints as a result, its HP is set
    to zero.

    **Parameters**

    - ``divisor``: The divisor used to calculate swap-out damage (e.g. 8 for
      one-eighth of max HP).

    **Example**

    .. code-block:: json

        "effects": [
            "harpooned 8"
        ]
    """

    name = "harpooned"
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
