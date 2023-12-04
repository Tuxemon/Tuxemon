# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.condition.condition import Condition
from tuxemon.db import Range
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique


class PricklyBackEffectResult(CondEffectResult):
    pass


@dataclass
class PricklyBackEffect(CondEffect):
    """

    Prickly:
    Each time you are hit by a Physical move
    the attacker takes 1/8th your maximum HP in damage

    """

    name = "prickly"

    def apply(
        self, tech: Condition, target: Monster
    ) -> PricklyBackEffectResult:
        done: bool = False
        assert tech.combat_state
        combat = tech.combat_state
        log = combat._log_action
        turn = combat._turn
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
                ):
                    if (
                        method.range == Range.touch
                        or method.range == Range.melee
                    ):
                        if action.target.instance_id == target.instance_id:
                            attacker = action.user
                            hit = True

        if tech.phase == "perform_action_status":
            if tech.slug == "prickly":
                if attacker and hit:
                    if attacker.current_hp > 0:
                        attacker.current_hp -= target.hp // 8
                        done = True
        return {
            "success": done,
            "condition": None,
            "technique": None,
            "extra": None,
        }
