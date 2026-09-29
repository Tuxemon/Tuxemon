# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase
from tuxemon.status.status import Status

if TYPE_CHECKING:
    from tuxemon.session import Session


@dataclass
class ChargingEffect(CoreEffect):
    """
    Applies the "charging" status to a monster.

    This effect clears existing statuses and, depending on the phase, applies
    a follow-up status when the monster uses a technique or an item.

    **Example**

    .. code-block:: json

        "effects": [
            "charging"
        ]
    """

    name = "charging"

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        host = status.host
        _statuses: list[Status] = []
        if status.has_phase(EffectPhase.PERFORM_TECH):
            host.status.clear_status(session)
            if status.on_tech_use:
                cond = Status.create(status.on_tech_use, host, host.steps)
                _statuses = [cond]
        if status.has_phase(EffectPhase.PERFORM_ITEM):
            host.status.clear_status(session)
            if status.on_item_use:
                cond = Status.create(status.on_item_use, host, host.steps)
                _statuses = [cond]
        return StatusEffectResult(
            name=status.name, success=True, statuses=_statuses
        )
