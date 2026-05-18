# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.locale.locale import T
from tuxemon.modifiers import parse_modifier_mode

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status

from tuxemon.db import EffectPhase


@dataclass
class PoisonedEffect(CoreEffect):
    """
    Applies the "poisoned" status effect.

    This effect reduces the target's HP over time based on a calculated
    damage multiplier. The amount of damage depends on the target's maximum
    HP and the chosen modifier evaluation strategy. If the calculated damage
    is greater than zero, the target becomes poisoned; otherwise, the status
    fails to apply and is cleared.

    **Parameters**

    - ``divisor``: Integer value used to determine base damage.
      - Damage is calculated as ``target.hp / divisor``.
    - ``mode``: Strategy used to evaluate modifiers against the target.
      Must be one of:
      - ``first``: Uses the first applicable modifier.
      - ``weakest``: Uses the weakest modifier.
      - ``strongest``: Uses the strongest modifier.
      - ``average``: Uses the average of all modifiers.
      - ``cumulative``: Uses the cumulative effect of all modifiers.

    **Example**

    .. code-block:: json

        "effects": [
            "poisoned 4 strongest"
        ]
    """

    name = "poisoned"
    divisor: int
    mode: str

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        poisoned: bool = False
        host = status.host
        params = {"target": host.name, "method": status.name}
        if status.has_phase(EffectPhase.PERFORM_STATUS):
            damage = host.hp / self.divisor
            mode_enum = parse_modifier_mode(self.mode)
            mult = status.modifiers.get_multiplier(host, mode=mode_enum)
            damage *= mult
            if damage > 0:
                poisoned = True
                host.current_hp = max(0, host.current_hp - int(damage))
            else:
                status.use_failure = T.format("combat_state_immune", params)
                host.status.clear_status(session)
        if status.has_phase(EffectPhase.ON_STEP_INTERVAL):
            hp_change = status.step_engine.compute_hp_change(host, ticks=1)
            if hp_change != 0:
                host.current_hp = max(0, host.current_hp + hp_change)
                return StatusEffectResult(name=status.name, success=True)

        return StatusEffectResult(name=status.name, success=poisoned)
