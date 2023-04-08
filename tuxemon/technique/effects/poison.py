# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass

from tuxemon import formula
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class PoisonEffectResult(TechEffectResult):
    pass


@dataclass
class PoisonEffect(TechEffect):
    """
    This effect has a chance to apply the poison status effect.
    """

    name = "poison"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> PoisonEffectResult:
        player = self.session.player
        value = float(player.game_variables["random_tech_hit"])
        potency = random.random()
        success = tech.potency >= potency and tech.accuracy >= value
        if success:
            status = Technique()
            status.load("status_poison")
            if self.objective == "user":
                user.apply_status(status)
            elif self.objective == "target":
                target.apply_status(status)
            return {
                "success": True,
            }

        if tech.slug == "status_poison":
            damage = formula.simple_poison(target)
            target.current_hp -= damage

            return {
                "success": bool(damage),
            }

        return {"success": False}
