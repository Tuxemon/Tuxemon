# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.combat import fainted
from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.condition.condition import Condition
from tuxemon.db import Range
from tuxemon.formula import simple_damage_calculate
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition


class RetaliateEffectResult(CondEffectResult):
    pass


@dataclass
class RetaliateEffect(CondEffect):
    """

    Retaliate:
    Keep track of all damage you take between entering
    this state and next doing damage. You do additional
    damage equal to damage taken.

    """

    name = "retaliate"

    def apply(
        self, condition: Condition, target: Monster
    ) -> RetaliateEffectResult:
        done: bool = False
        assert condition.combat_state
        combat = condition.combat_state
        log = combat._action_queue.history
        turn = combat._turn
        # check log actions
        attacker: Union[Monster, None] = None
        damage: int = 0
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
                    and action.target.instance_id == target.instance_id
                    and method.range != Range.special
                ):
                    attacker = action.user
                    hit = True
                    dam, mul = simple_damage_calculate(
                        method, attacker, target
                    )
                    damage = dam

        if (
            condition.phase == "perform_action_status"
            and attacker
            and hit
            and not fainted(attacker)
        ):
            attacker.current_hp -= damage
            done = True
        return {
            "success": done,
            "condition": None,
            "technique": None,
            "extra": None,
        }
