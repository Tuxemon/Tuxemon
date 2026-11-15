# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase
from tuxemon.locale.locale import T
from tuxemon.modifiers import parse_modifier_mode

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class BurntEffect(CoreEffect):
    """
    Applies the burnt status to a target based on a calculated damage multiplier.

    **Parameters**

    - ``divisor``: Determines how much HP is lost. Damage is calculated as
      ``target.hp / divisor``.
    - ``mode``: Strategy used to evaluate modifiers against the target.
      Must be one of: ``first``, ``weakest``, ``strongest``, ``average``,
      or ``cumulative``.

    **Example**

    .. code-block:: json

        "effects": [
            "burnt 4 strongest"
        ]
    """

    name = "burnt"
    divisor: int
    mode: str

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        burnt: bool = False
        host = status.host
        params = {"target": host.name, "method": status.name}
        if status.has_phase(EffectPhase.PERFORM_STATUS):
            damage = host.hp / self.divisor
            mode_enum = parse_modifier_mode(self.mode)
            mult = status.modifiers.get_multiplier(host, mode=mode_enum)
            damage *= mult
            if damage > 0:
                burnt = True
                host.current_hp = max(0, host.current_hp - int(damage))
            else:
                status.use_failure = T.format("combat_state_immune", params)
                host.status.clear_status(session)
        if status.has_phase(EffectPhase.ON_STEP_INTERVAL):
            hp_change = status.step_engine.compute_hp_change(host, ticks=1)
            if hp_change != 0:
                host.current_hp = max(0, host.current_hp + hp_change)
                return StatusEffectResult(name=status.name, success=True)

        return StatusEffectResult(name=status.name, success=burnt)
