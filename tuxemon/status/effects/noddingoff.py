# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.locale import T
from tuxemon.status.statuseffect import StatusEffect, StatusEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.status.status import Status


@dataclass
class NoddingOffEffect(StatusEffect):
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

    def apply(self, status: Status, target: Monster) -> StatusEffectResult:
        extra: list[str] = []
        tech: list[Technique] = []

        if status.phase == "pre_checking" and status.repl_tech:
            skip = Technique()
            skip.load(status.repl_tech)
            tech = [skip]

        if status.phase == "perform_action_tech" and self.wake_up(status):
            params = {"target": target.name.upper()}
            extra = [T.format("combat_state_dozing_end", params)]
            target.status.clear()
        return StatusEffectResult(
            name=status.name,
            success=True,
            statuses=[],
            techniques=tech,
            extras=extra,
        )

    def wake_up(self, status: Status) -> bool:
        if (
            status.duration >= status.nr_turn > 0
            and random.random() > self.chance
        ):
            return True
        if status.nr_turn > status.duration:
            return True
        return False
