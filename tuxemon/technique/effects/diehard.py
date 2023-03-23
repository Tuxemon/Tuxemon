# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class DieHardEffectResult(TechEffectResult):
    pass


@dataclass
class DieHardEffect(TechEffect):
    """
    This effect has a chance to apply the diehard status effect.
    """

    name = "diehard"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> DieHardEffectResult:
        player = self.session.player
        potency = random.random()
        value = float(player.game_variables["random_tech_hit"])
        success = tech.potency >= potency and tech.accuracy >= value
        if success:
            tech = Technique("status_diehard")
            user.apply_status(tech)
            return {"success": True}
        if tech.slug == "status_diehard":
            return {"success": True}

        return {"success": False}
