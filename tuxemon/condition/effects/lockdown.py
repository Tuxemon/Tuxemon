# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


@dataclass
class LockdownEffect(CondEffect):
    """
    This effect has a chance to apply the lockdown status effect.
    """

    name = "lockdown"

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        extra: list[str] = []
        if condition.phase == "enqueue_item":
            params = {"target": target.name.upper()}
            extra = [T.format("combat_state_lockdown_item", params)]
        return CondEffectResult(
            name=condition.name,
            success=True,
            conditions=[],
            techniques=[],
            extras=extra,
        )
