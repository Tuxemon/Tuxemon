# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from tuxemon.combat import fainted
from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.condition.condition import Condition
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique


@dataclass
class ElementalShieldBackEffect(CondEffect):
    """

    Elemental Shield:
    Each time you are hit by a Special move
    the attacker takes 1/16th your maximum HP in damage

    Parameters:
        divisor: The divisor.

    """

    name = "elemental_shield"
    divisor: int
    ranges: str

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        done: bool = False
        assert condition.combat_state
        combat = condition.combat_state
        log = combat._action_queue.history
        turn = combat._turn
        ranges = self.ranges.split(":")
        # check log actions
        attacker: Union[Monster, None] = None
        hit: bool = False
        for ele in log:
            _turn, action = ele
            if _turn == turn:
                method = action.method
                # progress
                if (
                    isinstance(method, Technique)
                    and isinstance(action.user, Monster)
                    and method.hit
                    and method.range in ranges
                    and action.target.instance_id == target.instance_id
                ):
                    attacker = action.user
                    hit = True

        if (
            condition.phase == "perform_action_status"
            and attacker
            and hit
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
