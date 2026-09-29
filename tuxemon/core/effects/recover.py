# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase
from tuxemon.formula import simple_recover
from tuxemon.locale.locale import T

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class RecoverEffect(CoreEffect):
    """
    Applies the "recover" status effect.

    This effect restores HP to the host monster based on a divisor of its
    maximum HP. Recovery may clear the status once the monster is fully
    healed.

    **Parameters**

      - ``divisor``: Integer value used to calculate the recovery amount.
      - Healing is determined by dividing the host's maximum HP by this
        divisor.

    **Example**

    .. code-block:: json

        "effects": [
            "recover 4"
        ]
    """

    name = "recover"
    divisor: int

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        extra: list[str] = []
        healing: bool = False
        host = status.host
        if status.has_phase(EffectPhase.PERFORM_STATUS):
            heal = simple_recover(host, self.divisor)
            host.current_hp = min(host.hp, host.current_hp + heal)
            healing = bool(heal)
        # check for recover (completely healed)
        if (
            status.has_phase(EffectPhase.CHECK_PARTY_HP)
            and host.current_hp >= host.hp
        ):
            host.status.clear_status(session)
            # avoid "overcome" hp bar
            if host.current_hp > host.hp:
                host.current_hp = host.hp
            params = {"target": host.name.upper()}
            extra = [T.format("combat_state_recover_failure", params)]

        return StatusEffectResult(
            name=status.name, success=healing, extras=extra
        )
