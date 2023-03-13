# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass

from tuxemon import formula
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class RecoverEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool


@dataclass
class RecoverEffect(TechEffect):
    """
    This effect has a chance to apply the recovering status effect.
    """

    name = "recover"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> RecoverEffectResult:
        player = self.session.player
        value = float(player.game_variables["random_tech_hit"])
        potency = random.random()
        success = tech.potency >= potency and tech.accuracy >= value
        if success:
            tech = Technique("status_recover", link=user)
            user.apply_status(tech)
            return {
                "damage": 0,
                "should_tackle": bool(success),
                "success": True,
            }

        # avoids Nonetype situation and reset the user
        if user is None:
            user = tech.link
            assert user
            heal = formula.simple_recover(user)
            user.current_hp += heal
        else:
            heal = formula.simple_recover(user)
            user.current_hp += heal

        return {
            "damage": heal,
            "should_tackle": False,
            "success": bool(heal),
        }
