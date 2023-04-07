# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class OverfeedEffectResult(TechEffectResult):
    pass


@dataclass
class OverfeedEffect(TechEffect):
    """
    This effect has a chance to apply the overfeed status effect.
    """

    name = "overfeed"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> OverfeedEffectResult:
        player = self.session.player
        potency = random.random()
        value = float(player.game_variables["random_tech_hit"])
        obj = self.objective
        success = tech.potency >= potency and tech.accuracy >= value
        if success:
            status = Technique()
            status.load("status_overfeed")
            if obj == "user":
                user.apply_status(status)
            elif obj == "target":
                target.apply_status(status)
            return {"success": True}

        return {"success": False}
