# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.combat import fainted
from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.condition.condition import Condition
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique


@dataclass
class ElementalShieldBackEffect(CondEffect):
    """
    Elemental Shield:
    Each time you are hit by a Special move the attacker takes damage equal to
    your maximum HP divided by the divisor.

    Parameters:
        divisor: The divisor used to calculate the damage.
        ranges: The ranges of moves that trigger the effect.
    """

    name = "elemental_shield"
    divisor: int
    ranges: str

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        done: bool = False
        ranges = self.ranges.split(":")
        assert condition.combat_state
        combat = condition.combat_state
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
                condition.phase == "perform_action_status"
                and method.hit
                and method.range in ranges
                and action.target.instance_id == target.instance_id
                and not fainted(attacker)
            ):
                damage = target.hp // self.divisor
                attacker.current_hp = max(0, attacker.current_hp - damage)
                done = True
        return CondEffectResult(
            name=condition.name,
            success=done,
            conditions=[],
            techniques=[],
            extras=[],
        )
