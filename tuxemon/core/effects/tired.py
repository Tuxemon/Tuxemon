# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class TiredEffect(CoreEffect):
    """
    Tired status

    """

    name = "tired"

    def apply_status(
        self,
        session: Session,
        status: Status,
    ) -> StatusEffectResult:
        extra: list[str] = []
        host = status.get_host()
        if status.has_phase(EffectPhase.PERFORM_TECH):
            params = {"target": host.name.upper()}
            extra = [T.format("combat_state_tired_end", params)]
            host.status.clear_status(session)
        return StatusEffectResult(name=status.name, success=True, extras=extra)
