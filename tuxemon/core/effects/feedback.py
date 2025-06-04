# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class FeedBackEffect(CoreEffect):
    """
    Each time you are hit by a Special move the attacker takes damage equal to
    your maximum HP divided by the divisor.

    Parameters:
        divisor: The divisor used to calculate the damage.
        ranges: The ranges of moves that trigger the effect.
    """

    name = "feedback"
    divisor: int
    ranges: str

    def apply_status_target(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        done: bool = False
        ranges = self.ranges.split(":")
        assert status.combat_state
        combat = status.combat_state
        log = combat._action_queue
        turn = combat._turn
        action = log.get_last_action(turn, target, "target")

        if (
            action
            and isinstance(action.method, Technique)
            and isinstance(action.user, Monster)
        ):
            method = action.method
            attacker = action.user

            if (
                status.phase == "perform_action_status"
                and method.hit
                and method.range in ranges
                and action.target.instance_id == target.instance_id
                and not attacker.is_fainted
            ):
                damage = target.hp // self.divisor
                attacker.current_hp = max(0, attacker.current_hp - damage)
                done = True
        return StatusEffectResult(name=status.name, success=done)
