# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.formula import simple_recover
from tuxemon.locale import T
from tuxemon.status.statuseffect import StatusEffect, StatusEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.status.status import Status


@dataclass
class RecoverEffect(StatusEffect):
    """
    This effect has a chance to apply the recovering status effect.

    Parameters:
        divisor: The number by which user HP is to be divided.

    """

    name = "recover"
    divisor: int

    def apply(self, status: Status, target: Monster) -> StatusEffectResult:
        extra: list[str] = []
        healing: bool = False
        if status.phase == "perform_action_status":
            user = status.link
            assert user
            heal = simple_recover(user, self.divisor)
            user.current_hp = min(user.hp, user.current_hp + heal)
            healing = bool(heal)
        # check for recover (completely healed)
        if status.phase == "check_party_hp" and target.current_hp >= target.hp:
            target.status.clear()
            # avoid "overcome" hp bar
            if target.current_hp > target.hp:
                target.current_hp = target.hp
            params = {"target": target.name.upper()}
            extra = [T.format("combat_state_recover_failure", params)]

        return StatusEffectResult(
            name=status.name,
            success=healing,
            statuses=[],
            techniques=[],
            extras=extra,
        )
