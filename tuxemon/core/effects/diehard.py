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
class DieHardEffect(CoreEffect):
    """
    DieHard: When HP would fall below 1, set it to 1, remove this status and
    print "X fights through the pain."

    A monster that is already on exactly 1 HP cannot gain the Diehard status.

    Parameters:
        hp: The amount of HP to set.
    """

    name = "diehard"
    hp: int

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        extra: list[str] = []
        host = status.get_host()
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
