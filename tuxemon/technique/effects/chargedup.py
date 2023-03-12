# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class ChargedUpEffectResult(TechEffectResult):
    pass


@dataclass
class ChargedUpEffect(TechEffect):
    """
    This effect has a chance to apply the charged up status effect.
    """

    name = "chargedup"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> ChargedUpEffectResult:
        player = self.session.player
        potency = random.random()
        value = float(player.game_variables["random_tech_hit"])
        obj = self.objective
        success = tech.potency >= potency and tech.accuracy >= value
        if success:
            tech = Technique()
            tech.load("status_chargedup")
            if obj == "user":
                user.apply_status(tech)
            elif obj == "target":
                target.apply_status(tech)
            return {"success": True}

        return {"success": False}
