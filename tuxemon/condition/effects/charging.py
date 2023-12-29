# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.condition.condition import Condition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


class ChargingEffectResult(CondEffectResult):
    pass


@dataclass
class ChargingEffect(CondEffect):
    """
    Charging status

    """

    name = "charging"

    def apply(
        self, condition: Condition, target: Monster
    ) -> ChargingEffectResult:
        player = target.owner
        assert player
        cond: Optional[Condition] = None
        if condition.phase == "perform_action_tech":
            target.status.clear()
            if condition.repl_tech:
                cond = Condition()
                cond.load(condition.repl_tech)
                cond.steps = player.steps
                cond.link = target
        if condition.phase == "perform_action_item":
            target.status.clear()
            if condition.repl_item:
                cond = Condition()
                cond.load(condition.repl_item)
                cond.steps = player.steps
                cond.link = target
        return {
            "success": True,
            "condition": cond,
            "technique": None,
            "extra": None,
        }
