# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from tuxemon.db import Range
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class FlameShieldEffectResult(TechEffectResult):
    pass


@dataclass
class FlameShieldEffect(TechEffect):
    """
    Flame Shield:

    Creatures that hit you with a melee or touch attack
    take 1/16 your maximum hit points in damage.

    """

    name = "flame_shield"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> FlameShieldEffectResult:
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
                        method.range == Range.touch
                        or method.range == Range.melee
                    ):
                        if action.target.instance_id == target.instance_id:
                            attacker = action.user
                            hit = True

        if tech.slug == "status_flameshield" and hit:
            if attacker:
                if attacker.current_hp > 0:
                    attacker.current_hp -= target.hp // 16
                    return {"success": True}
                else:
                    return {"success": False}
            else:
                return {"success": False}
        else:
            return {"success": False}
