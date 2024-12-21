# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


@dataclass
class FlinchingEffect(CondEffect):
    """
    Flinching: 50% chance to miss your next turn.
    If you do miss your next turn, this condition ends.

    Parameters:
        chance: The chance.

    """

    name = "flinching"
    chance: float

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        tech: list[Technique] = []
        if condition.phase == "pre_checking" and random.random() > self.chance:
            user = condition.link
            empty = condition.repl_tech
            assert user and empty
            skip = Technique()
            skip.load(empty)
            tech = [skip]
            user.status.clear()
        return CondEffectResult(
            name=condition.name,
            success=True,
            conditions=[],
            techniques=tech,
            extras=[],
        )
