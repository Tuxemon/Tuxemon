# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import fainted
from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.db import Range
from tuxemon.formula import simple_damage_calculate
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition


@dataclass
class RevengeEffect(CondEffect):
    """
    Revenge:
    The next time you are attacked, the attacker takes the same amount of
    damage that you receive. Additionally, you heal for the amount of
    damage you dealt in the previous turn.

    Note: This effect is triggered only once, after which it is removed.
    """

    name = "revenge"

    def apply(self, condition: Condition, target: Monster) -> CondEffectResult:
        done: bool = False
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
            dam, mul = simple_damage_calculate(method, attacker, target)

            if (
                condition.phase == "perform_action_status"
                and method.hit
                and action.target.instance_id == target.instance_id
                and method.range != Range.special
                and not fainted(attacker)
            ):
                attacker.current_hp = max(0, attacker.current_hp - dam)
                target.current_hp = min(target.hp, target.current_hp + dam)
                done = True
        return CondEffectResult(
            name=condition.name,
            success=done,
            conditions=[],
            techniques=[],
            extras=[],
        )
