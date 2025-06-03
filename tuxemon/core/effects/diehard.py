# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import fainted
from tuxemon.core.core_effect import StatusEffect, StatusEffectResult
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class DieHardEffect(StatusEffect):
    """
    DieHard: When HP would fall below 1, set it to 1, remove this status and
    print "X fights through the pain."

    A monster that is already on exactly 1 HP cannot gain the Diehard status.

    Parameters:
        hp: The amount of HP to set.
    """

    name = "diehard"
    hp: int

    def apply(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        extra: list[str] = []
        if status.phase == "check_party_hp":
            params = {"target": target.name.upper()}
            if fainted(target):
                target.current_hp = self.hp
                target.status.clear()
                extra = [T.format("combat_state_diehard_tech", params)]
            if target.current_hp == self.hp:
                target.status.clear()
                extra = [T.format("combat_state_diehard_end", params)]

        return StatusEffectResult(name=status.name, success=True, extras=extra)
