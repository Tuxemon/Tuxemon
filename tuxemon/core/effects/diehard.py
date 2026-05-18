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
class DieHardEffect(CoreEffect):
    """
    Applies the "diehard" status to a monster.

    This effect prevents a monster from fainting by keeping its HP at 1 when
    it would otherwise drop below that threshold. The status is then removed,
    and a combat message is displayed.

    **Parameters**

    - ``hp``: The minimum HP value to enforce (typically ``1``).

    **Example**

    .. code-block:: json

        "effects": [
            "diehard 1"
        ]
    """

    name = "diehard"
    hp: int

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        extra: list[str] = []
        host = status.host
        if status.has_phase(EffectPhase.CHECK_PARTY_HP):
            params = {"target": host.name.upper()}
            if host.current_hp == self.hp:
                host.status.clear_status(session)
                extra = [T.format("combat_state_diehard_end", params)]
            if host.is_fainted:
                host.current_hp = self.hp
                host.status.clear_status(session)
                extra = [T.format("combat_state_diehard_tech", params)]
        return StatusEffectResult(name=status.name, success=True, extras=extra)
