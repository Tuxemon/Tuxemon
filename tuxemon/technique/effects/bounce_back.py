# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from tuxemon.db import Range
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class BounceBackEffectResult(TechEffectResult):
    pass


@dataclass
class BounceBackEffect(TechEffect):
    """
    Applies prickly and feedback.

    Prickly:
    Each time you are hit by a Physical move
    the attacker takes 1/8th your maximum HP in damage

    Feedback:
    Each time you are hit by a Special move
    the attacker takes 1/8th your maximum HP in damage

    """

    name = "bounce_back"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> BounceBackEffectResult:
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
                method = action.technique
                # progress
                if (
                    isinstance(method, Technique)
                    and isinstance(action.user, Monster)
                    and method.hit
                ):
                    if (
                        self.objective == "feedback"
                        and method.range == Range.special
                    ):
                        if action.target.instance_id == target.instance_id:
                            attacker = action.user
                            hit = True
                    elif (
                        self.objective == "prickly"
                        and method.range != Range.special
                    ):
                        if action.target.instance_id == target.instance_id:
                            attacker = action.user
                            hit = True

        if tech.slug == "status_feedback" or tech.slug == "status_prickly":
            if attacker and hit:
                if attacker.current_hp > 0:
                    attacker.current_hp -= target.hp // 8
                    return {"success": True}
                else:
                    return {"success": False}
            else:
                return {"success": False}
        else:
            return {"success": False}
