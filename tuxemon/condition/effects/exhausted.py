# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.condition.condition import Condition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class ExhaustedEffect(CondEffect):
    """
    Exhausted status

    """

    name = "exhausted"

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        player = target.owner
        assert player
        _condition: list[Condition] = []
        if condition.phase == "perform_action_tech":
            target.status.clear()
            if condition.repl_tech:
                cond = Condition()
                cond.load(condition.repl_tech)
                cond.steps = player.steps
                cond.link = target
                _condition = [cond]
        return CondEffectResult(
            name=condition.name,
            success=True,
            condition=_condition,
            technique=[],
            extra=[],
        )
