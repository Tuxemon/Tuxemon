# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase
from tuxemon.locale.locale import T

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class LockdownEffect(CoreEffect):
    """
    Applies the "lockdown" status effect.

    This effect restricts the target monster's ability to use items during
    combat. When triggered, it generates a translated message indicating
    that the target is under lockdown.

    **Example**

    .. code-block:: json

        "effects": [
            "lockdown"
        ]
    """

    name = "lockdown"

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        extra: list[str] = []
        host = status.host
        if status.has_phase(EffectPhase.ENQUEUE_ITEM):
            params = {"target": host.name.upper()}
            extra = [T.format("combat_state_lockdown_item", params)]
        return StatusEffectResult(name=status.name, success=True, extras=extra)
