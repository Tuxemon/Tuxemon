# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.locale import T
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


@dataclass
class NoddingOffEffect(CondEffect):
    """
    This effect has a chance to apply the nodding off status effect.

    Sleep lasts for a minimum of one turn.
    It has a 50% chance to end after each turn.
    If it has gone on for 5 turns, it ends.

    Parameters:
        chance: The chance.

    """

    name = "noddingoff"
    chance: float

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        extra: list[str] = []
        tech: list[Technique] = []

        if condition.phase == "pre_checking" and condition.repl_tech:
            skip = Technique()
            skip.load(condition.repl_tech)
            tech = [skip]

        if condition.phase == "perform_action_tech" and self.wake_up(
            condition
        ):
            params = {"target": target.name.upper()}
            extra = [T.format("combat_state_dozing_end", params)]
            target.status.clear()
        return CondEffectResult(
            name=condition.name,
            success=True,
            conditions=[],
            techniques=tech,
            extras=extra,
        )

    def wake_up(self, condition: Condition) -> bool:
        if (
            condition.duration >= condition.nr_turn > 0
            and random.random() > self.chance
        ):
            return True
        if condition.nr_turn > condition.duration:
            return True
        return False
