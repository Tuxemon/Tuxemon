# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.locale import T
from tuxemon.modifiers import parse_modifier_mode

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status

from tuxemon.db import EffectPhase


@dataclass
class PoisonedEffect(CoreEffect):
    """
    This effect has a chance to apply the poisoned status based on a calculated
    damage multiplier.

    Parameters:
        divisor: Determines how much HP is lost (damage is calculated as
            target.hp / divisor).
        mode: Specifies the strategy used to evaluate modifiers against
            the target. Must be one of: "first", "weakest", "strongest",
            "average", "cumulative".

    The effect checks whether a damage multiplier applies to the target using
    the given mode. If the calculated damage is greater than zero, the target
    is poisoned and loses HP. Otherwise, the status fails to apply and is cleared.
    """

    name = "poisoned"
    divisor: int
    mode: str

    def apply_status_target(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        poisoned: bool = False
        params = {"target": target.name, "method": status.name}
        if status.has_phase(EffectPhase.PERFORM_STATUS):
            damage = target.hp / self.divisor
            mode_enum = parse_modifier_mode(self.mode)
            mult = status.modifiers.get_multiplier(target, mode=mode_enum)
            damage *= mult
            if damage > 0:
                poisoned = True
                target.current_hp = max(0, target.current_hp - int(damage))
            else:
                status.use_failure = T.format("combat_state_immune", params)
                target.status.clear_status(session)

        return StatusEffectResult(name=status.name, success=poisoned)
