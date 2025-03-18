# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import fainted
from tuxemon.db import Range
from tuxemon.formula import simple_damage_calculate
from tuxemon.monster import Monster
from tuxemon.status.statuseffect import StatusEffect, StatusEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.status.status import Status


@dataclass
class RevengeEffect(StatusEffect):
    """
    Revenge:
    The next time you are attacked, the attacker takes the same amount of
    damage that you receive. Additionally, you heal for the amount of
    damage you dealt in the previous turn.

    Note: This effect is triggered only once, after which it is removed.
    """

    name = "revenge"

    def apply(self, status: Status, target: Monster) -> StatusEffectResult:
        done: bool = False
        assert status.combat_state
        combat = status.combat_state
        log = combat._action_queue
        turn = combat._turn
        action = log.get_last_action(turn, target, "target")

        if (
            action
            and isinstance(action.method, Technique)
            and isinstance(action.user, Monster)
            and action.method.range != Range.special
        ):
            method = action.method
            attacker = action.user
            dam, mul = simple_damage_calculate(method, attacker, target)

            if (
                status.phase == "perform_action_status"
                and method.hit
                and action.target.instance_id == target.instance_id
                and method.range != Range.special
                and not fainted(attacker)
            ):
                attacker.current_hp = max(0, attacker.current_hp - dam)
                target.current_hp = min(target.hp, target.current_hp + dam)
                done = True
        return StatusEffectResult(
            name=status.name,
            success=done,
            statuses=[],
            techniques=[],
            extras=[],
        )
