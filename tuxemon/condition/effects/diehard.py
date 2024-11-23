# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import fainted
from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


@dataclass
class DieHardEffect(CondEffect):
    """
    DieHard: When HP would fall below 1, set it to 1, remove this condition and
    print "X fights through the pain."

    A monster that is already on exactly 1 HP cannot gain the Diehard condition.

    Parameters:
        hp: The amount of HP to set.

    """

    name = "diehard"
    hp: int

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        extra: list[str] = []
        if condition.phase == "check_party_hp":
            params = {"target": target.name.upper()}
            if fainted(target):
                target.current_hp = self.hp
                target.status.clear()
                extra = [T.format("combat_state_diehard_tech", params)]
            if target.current_hp == self.hp:
                target.status.clear()
                extra = [T.format("combat_state_diehard_end", params)]

        return CondEffectResult(
            name=condition.name,
            success=True,
            conditions=[],
            techniques=[],
            extras=extra,
        )
