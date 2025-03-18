# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.locale import T
from tuxemon.status.statuseffect import StatusEffect, StatusEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.status.status import Status


@dataclass
class LockdownEffect(StatusEffect):
    """
    This effect has a chance to apply the lockdown status effect.
    """

    name = "lockdown"

    def apply(self, status: Status, target: Monster) -> StatusEffectResult:
        extra: list[str] = []
        if status.phase == "enqueue_item":
            params = {"target": target.name.upper()}
            extra = [T.format("combat_state_lockdown_item", params)]
        return StatusEffectResult(
            name=status.name,
            success=True,
            statuses=[],
            techniques=[],
            extras=extra,
        )
