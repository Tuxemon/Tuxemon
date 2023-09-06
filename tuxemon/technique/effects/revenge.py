# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from tuxemon.db import Range
from tuxemon.formula import simple_damage_calculate
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class RevengeEffectResult(TechEffectResult):
    pass


@dataclass
class RevengeEffect(TechEffect):
    """

    Revenge:
    The next time you are attacked, your enemy takes
    the same amount of damage that you do. You heal as
    much damage as you dealt.

    """

    name = "revenge"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> RevengeEffectResult:
        done: bool = False
        assert tech.combat_state
        combat = tech.combat_state
        log = combat._log_action
        turn = combat._turn
        # check log actions
        attacker: Union[Monster, None] = None
        damage: int = 0
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
                        action.target.instance_id == target.instance_id
                        and method.range != Range.special
                    ):
                        attacker = action.user
                        hit = True
                        dam, mul = simple_damage_calculate(
                            method, attacker, target
                        )
                        damage = dam

        if tech.slug == "revenge":
            if attacker and hit:
                if attacker.current_hp > 0:
                    attacker.current_hp -= damage
                    target.current_hp += damage
                    done = True
        return {"success": done, "extra": None}
