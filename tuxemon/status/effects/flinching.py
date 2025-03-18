# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.status.statuseffect import StatusEffect, StatusEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.status.status import Status


@dataclass
class FlinchingEffect(StatusEffect):
    """
    Flinching: 50% chance to miss your next turn.
    If you do miss your next turn, this status ends.

    Parameters:
        chance: The chance.

    """

    name = "flinching"
    chance: float

    def apply(self, status: Status, target: Monster) -> StatusEffectResult:
        tech: list[Technique] = []
        if status.phase == "pre_checking" and random.random() > self.chance:
            user = status.link
            empty = status.repl_tech
            assert user and empty
            skip = Technique()
            skip.load(empty)
            tech = [skip]
            user.status.clear()
        return StatusEffectResult(
            name=status.name,
            success=True,
            statuses=[],
            techniques=tech,
            extras=[],
        )
